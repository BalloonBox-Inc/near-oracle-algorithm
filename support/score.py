from support.models import *
from support.helper import *


def plaid_score(score_range, feedback, model_weights, model_penalties, metric_weigths, params, txn):

    credit, feedback = credit_mix(txn, feedback)

    if credit == 0:
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = list(model_penalties.values())

    else:
        credit, feedback = plaid_credit(txn, feedback)
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        a = list(model_weights.values())

    b = [credit, velocity, stability, diversity]

    head, tail = head_tail_list(score_range)
    score = tail + (head-tail)*(dot_product(a, b))

    return score, feedback


def coinbase_score(score_range, feedback, model_weights, metric_weigths, params, acc, txn):

    params = coinbase_params(params, score_range)

    kyc, feedback = coinbase_kyc(acc, txn, feedback)
    history, feedback = coinbase_history(acc, feedback, params)
    liquidity, feedback = coinbase_liquidity(
        acc, txn, feedback, metric_weigths, params)
    activity, feedback = coinbase_activity(
        acc, txn, feedback, metric_weigths, params)

    a = list(model_weights.values())
    b = [kyc, history, liquidity, activity]

    head, tail = head_tail_list(score_range)
    score = tail + (head-tail)*(dot_product(a, b))

    return score, feedback
