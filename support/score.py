from support.models import *
from support.helper import *


def plaid_score(txn, feedback):

    mix, feedback = credit_mix(txn, feedback)

    if mix == 0:
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        # adds up to 0.95 for lack of credit card - it's a penalty
        score = 300 + 600*(0.33*velocity + 0.42*stability + 0.20*diversity)

    else:
        credit, feedback = plaid_credit(txn, feedback)
        velocity, feedback = plaid_velocity(txn, feedback)
        stability, feedback = plaid_stability(txn, feedback)
        diversity, feedback = plaid_diversity(txn, feedback)

        score = 300 + 600*(0.42*credit + 0.20*velocity +
                           0.28*stability + 0.10*diversity)

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

    score = 300 + 600*(dot_product(a, b))

    return score, feedback
