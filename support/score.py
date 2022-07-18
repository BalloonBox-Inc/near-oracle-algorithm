from support.models import *
from support.helper import *
from datetime import datetime
from icecream import ic


NOW = datetime.now().date()


def plaid_score(
    data, score_range, feedback, model_weights, model_penalties, metric_weigths, params
):
    txn = data["transactions"]
    acc = data["accounts"]
    txn = merge_dict(txn, acc, "account_id", ["type", "subtype"])
    txn = sorted(txn, key=lambda d: d["date"])

    # transactions
    credit = filter_dict(txn, "type", "credit")
    depository = filter_dict(txn, "type", "depository")
    savings = filter_dict(txn, "subtype", "savings")
    checking = filter_dict(txn, "subtype", "checking")

    # account age in months
    longevity = abs((NOW - checking[0]["date"]).days)
    feedback["stability"]["txn_history"] = longevity
    longevity = longevity / 30
    ic(longevity)

    # transactions count
    volume = len(checking)
    ic(volume)

    # monthly transactions
    m_volume = volume / longevity
    ic(m_volume)

    # monthly balance
    m_amount = sum(d["amount"] for d in checking) / longevity
    ic(m_amount)

    # accounts
    cred = [d for d in acc if d["type"].lower() == "credit"]
    dep = [d for d in acc if d["type"].lower() == "depository"]
    n_dep = [d for d in acc if d["type"].lower() != "depository"]

    params = plaid_params(params, score_range)

    credit, feedback = credit_mix(txn, cred, feedback, params)

    if credit == 0:
        velocity, feedback = plaid_velocity(acc, txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(
            acc, txn, dep, n_dep, feedback, metric_weigths, params
        )
        diversity, feedback = plaid_diversity(
            acc, txn, feedback, metric_weigths, params
        )

        a = list(model_penalties.values())

    else:
        credit, feedback = plaid_credit(
            acc, txn, cred, feedback, metric_weigths, params
        )
        velocity, feedback = plaid_velocity(acc, txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(
            acc, txn, dep, n_dep, feedback, metric_weigths, params
        )
        diversity, feedback = plaid_diversity(
            acc, txn, feedback, metric_weigths, params
        )

        a = list(model_weights.values())

    b = [credit, velocity, stability, diversity]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback


def coinbase_score(
    score_range, feedback, model_weights, metric_weigths, params, acc, txn
):

    params = coinbase_params(params, score_range)

    kyc, feedback = coinbase_kyc(acc, txn, feedback)
    history, feedback = coinbase_history(acc, feedback, params)
    liquidity, feedback = coinbase_liquidity(acc, txn, feedback, metric_weigths, params)
    activity, feedback = coinbase_activity(acc, txn, feedback, metric_weigths, params)

    a = list(model_weights.values())
    b = [kyc, history, liquidity, activity]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback


def covalent_score(
    score_range,
    feedback,
    model_weights,
    metric_weigths,
    params,
    erc_rank,
    txn,
    balances,
    portfolio,
):

    params = covalent_params(params, score_range)

    credibility, feedback = covalent_credibility(
        txn, balances, portfolio, feedback, metric_weigths, params
    )
    wealth, feedback = covalent_wealth(
        txn, balances, feedback, metric_weigths, params, erc_rank
    )
    traffic, feedback = covalent_traffic(
        txn, portfolio, feedback, metric_weigths, params, erc_rank
    )
    stamina, feedback = covalent_stamina(
        txn, balances, portfolio, feedback, metric_weigths, params, erc_rank
    )

    a = list(model_weights.values())
    b = [credibility, wealth, traffic, stamina]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback
