from support.assessment import *
from support.models import *
from support.helper import *


# @evaluate_function
def plaid_score(data, score_range, feedback, model_weights, metric_weigths, params):

    # format params
    params = plaid_params(params, score_range)

    # split data: mutually exclusive
    credit_card = filter_dict(data, 'type', 'credit')
    checking = filter_dict(data, 'subtype', 'checking')
    savings = filter_dict(data, 'subtype', 'savings')

    # create metadata
    metadata = {
        'credit_card': {
            'general': {},
            'util_ratio': {},
            'late_payment': {}
        },
        'checking': {
            'general': {},
            'income': {},
            'expenses': {},
            'investments': {
                'earnings': {},
                'deposits': {},
                'withdrawals': {}
            }
        },
        'savings': {
            'general': {},
            'earnings': {},
            'cash_flow': {
                'deposits': {},
                'withdrawals': {}
            }
        }
    }

    if credit_card:
        credit_card = dict_reverse_cumsum(credit_card, 'amount', 'current')
        metadata = general(metadata, credit_card, 'credit_card')
        metadata = late_payment(metadata, credit_card)

    if checking:
        checking = dict_reverse_cumsum(checking, 'amount', 'current')
        metadata = general(metadata, checking, 'checking')
        metadata = income(metadata, checking, 'sub_category', 'payroll')
        metadata = expenses(metadata, checking, 'sub_category', 'rent')
        metadata = expenses(metadata, checking, 'sub_category', 'insurance')
        metadata = expenses(metadata, checking, 'sub_category', 'utilities')
        metadata = expenses(metadata, checking, 'sub2_category', 'loans and mortgages')
        metadata = investments(metadata, checking, 'sub2_category', 'financial planning and investments')

    if savings:
        savings = dict_reverse_cumsum(savings, 'amount', 'current')
        metadata = general(metadata, savings, 'savings')
        metadata = cash_flow(metadata, savings, 'category', 'interest')
        metadata = earnings(metadata, savings, 'sub_category', 'interest earned')

    # create model
    credit, feedback = plaid_credit_model(feedback, params, metric_weigths, metadata)
    velocity, feedback = plaid_velocity_model(feedback, params, metric_weigths, metadata)
    stability, feedback = plaid_stability_model(feedback, params, metric_weigths, metadata)
    diversity, feedback = plaid_diversity_model(feedback, params, metric_weigths,  metadata)

    a = list(model_weights.values())
    b = [credit, velocity, stability, diversity]

    head, tail = head_tail_list(score_range)
    score = head + (tail - head) * (dot_product(a, b))

    return score, feedback


# @evaluate_function
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


# @evaluate_function
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
