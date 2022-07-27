from support.assessment import *
from support.models import *
from support.metrics_plaid import *
from support.helper import *
from icecream import ic


# @evaluate_function
def plaid_score(data, score_range, feedback, model_weights, model_penalties, metric_weigths, params):

    txn = data['transactions']
    acc = data['accounts']
    dataset = format_plaid_data(txn, acc)

    feedback['stability']['txn_history'] = dataset[0]['timespan']

    credit_card = filter_dict(dataset, 'type', 'credit')
    checking = filter_dict(dataset, 'subtype', 'checking')
    savings = filter_dict(dataset, 'subtype', 'savings')

    metadata = {'credit_card': {}, 'checking': {}, 'savings': {}}
    if credit_card:
        credit_card = dict_reverse_cumsum(credit_card, 'amount', 'current')
        metadata = balances(metadata, credit_card, 'credit_card')
        metadata = transactions(metadata, credit_card, 'credit_card')
        metadata = late_payment(metadata, credit_card)
    if checking:
        checking = dict_reverse_cumsum(checking, 'amount', 'current')
        metadata = balances(metadata, checking, 'checking')
        metadata = transactions(metadata, checking, 'checking')
    if savings:
        savings = dict_reverse_cumsum(savings, 'amount', 'current')
        metadata = balances(metadata, savings, 'savings')
        metadata = transactions(metadata, savings, 'savings')

    # accounts
    cred = [d for d in acc if d['type'].lower() == 'credit']
    dep = [d for d in acc if d['type'].lower() == 'depository']
    n_dep = [d for d in acc if d['type'].lower() != 'depository']

    params = plaid_params(params, score_range)

    credit, feedback = credit_mix(txn, cred, feedback, params)  # name, account_id

    if credit == 0:
        velocity, feedback = plaid_velocity(acc, txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(acc, txn, dep, n_dep, feedback, metric_weigths, params)
        diversity, feedback = plaid_diversity(acc, txn, feedback, metric_weigths, params)

        a = list(model_penalties.values())

    else:
        credit, feedback = plaid_credit(acc, txn, cred, feedback, metric_weigths, params)  # limit, account_id
        velocity, feedback = plaid_velocity(acc, txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(acc, txn, dep, n_dep, feedback, metric_weigths, params)
        diversity, feedback = plaid_diversity(acc, txn, feedback, metric_weigths, params)

        a = list(model_weights.values())

    b = [credit, velocity, stability, diversity]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback


def coinbase_score(score_range, feedback, model_weights, metric_weigths, params, acc, txn):

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


def covalent_score(score_range, feedback, model_weights, metric_weigths, params, erc_rank, txn, balances, portfolio):

    params = covalent_params(params, score_range)

    credibility, feedback = covalent_credibility(txn, balances, portfolio, feedback, metric_weigths, params)
    wealth, feedback = covalent_wealth(txn, balances, feedback, metric_weigths, params, erc_rank)
    traffic, feedback = covalent_traffic(txn, portfolio, feedback, metric_weigths, params, erc_rank)
    stamina, feedback = covalent_stamina(txn, balances, portfolio, feedback, metric_weigths, params, erc_rank)

    a = list(model_weights.values())
    b = [credibility, wealth, traffic, stamina]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback
