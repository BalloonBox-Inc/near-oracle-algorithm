from support.metrics_plaid import *
from support.metrics_coinbase import *
from support.metrics_covalent import *
from support.helper import *


# -------------------------------------------------------------------------- #
#                                Plaid Model                                 #
# -------------------------------------------------------------------------- #
'''
    params = [
        due_date, duration, count_zero, count_invest, volume_credit, volume_invest,
        volume_balance, flow_ratio, slope, slope_lr, activity_vol_mtx,
        activity_cns_mtx, credit_mix_mtx, diversity_velo_mtx, fico_medians, count_lively,
        count_txn, volume_flow, volume_withdraw, volume_deposit, volume_min, 
        credit_util_pct, frequency_interest
    ]
'''


def plaid_credit(txn, feedback, weights, params):

    limit, feedback = credit_limit(
        txn,
        feedback,
        params[1],
        params[4],
        params[10]
    )

    util_ratio, feedback = credit_util_ratio(
        txn,
        feedback,
        params[1],
        params[21],
        params[11]
    )

    interest, feedback = credit_interest(
        txn,
        feedback,
        params[14],
        params[22]
    )

    length, feedback = credit_length(
        txn,
        feedback,
        params[14],
        params[1]
    )

    livelihood, feedback = credit_livelihood(
        txn,
        feedback,
        params[14],
        params[15]
    )

    a = list(weights.values())[:5]
    b = [limit, util_ratio, interest, length, livelihood]

    score = dot_product(a, b)

    return score, feedback


def plaid_velocity(txn, feedback, weights, params):

    withdrawals, feedback = velocity_withdrawals(
        txn,
        feedback,
        params[2],
        params[18],
        params[13]
    )

    deposits, feedback = velocity_deposits(
        txn,
        feedback,
        params[2],
        params[19],
        params[13]
    )

    net_flow, feedback = velocity_month_net_flow(
        txn,
        feedback,
        params[7],
        params[17],
        params[10]
    )

    txn_count, feedback = velocity_month_txn_count(
        txn,
        feedback,
        params[14],
        params[16]
    )

    slope, feedback = velocity_slope(
        txn,
        feedback,
        params[14],
        params[9],
        params[8],
        params[10]
    )

    a = list(weights.values())[5:10]
    b = [withdrawals, deposits, net_flow, txn_count, slope]

    score = dot_product(a, b)

    return score, feedback


def plaid_stability(txn, feedback, weights, params):

    balance, feedback = stability_tot_balance_now(
        txn,
        feedback,
        params[14],
        params[6]
    )

    feedback = stability_loan_duedate(
        txn,
        feedback,
        params[0]
    )

    run_balance, feedback = stability_min_running_balance(
        txn,
        feedback,
        params[1],
        params[20],
        params[11]
    )

    a = list(weights.values())[10:12]
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def plaid_diversity(txn, feedback, weights, params):

    acc_count, feedback = diversity_acc_count(
        txn,
        feedback,
        params[2],
        params[1],
        params[13]
    )

    profile, feedback = diversity_profile(
        txn,
        feedback,
        params[14],
        params[5]
    )

    a = list(weights.values())[12:]
    b = [acc_count, profile]

    score = dot_product(a, b)

    return score, feedback


# -------------------------------------------------------------------------- #
#                               Coinbase Model                               #
# -------------------------------------------------------------------------- #
'''
    params = [
        due_date, duration, volume_balance, volume_profit, count_txn, activity_vol_mtx, 
        activity_cns_mtx, fico_medians
    ]
'''



def coinbase_kyc(acc, txn, feedback):

    score, feedback = kyc(acc, txn, feedback)

    return score, feedback


def coinbase_history(acc, feedback, params):

    score, feedback = history_acc_longevity(
        acc,
        feedback,
        params[1],
        params[7]
    )

    return score, feedback


def coinbase_liquidity(acc, txn, feedback, weights, params):

    balance, feedback = liquidity_tot_balance_now(
        acc,
        feedback,
        params[2],
        params[7]
    )

    feedback = liquidity_loan_duedate(
        txn,
        feedback,
        params[0]
    )

    run_balance, feedback = liquidity_avg_running_balance(
        acc,
        txn,
        feedback,
        params[1],
        params[2],
        params[6]
    )

    a = list(weights.values())[:2]
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def coinbase_activity(acc, txn, feedback, weights, params):

    credit_volume, feedback = activity_tot_volume_tot_count(
        txn,
        'credit',
        feedback,
        params[2],
        params[4],
        params[5]
    )

    debit_volume, feedback = activity_tot_volume_tot_count(
        txn,
        'debit',
        feedback,
        params[2],
        params[4],
        params[5]
    )

    credit_consistency, feedback = activity_consistency(
        txn,
        'credit',
        feedback,
        params[1],
        params[3],
        params[6]
    )

    debit_consistency, feedback = activity_consistency(
        txn,
        'debit',
        feedback,
        params[1],
        params[3],
        params[6]
    )

    inception, feedback = activity_profit_since_inception(
        acc,
        txn,
        feedback,
        params[3],
        params[7]
    )

    a = list(weights.values())[2:]
    b = [credit_volume, debit_volume,
         credit_consistency, debit_consistency, inception]

    score = dot_product(a, b)

    return score, feedback


# -------------------------------------------------------------------------- #
#                               Covalent Model                               #
# -------------------------------------------------------------------------- #
'''
    params = [
        count_to_four, volume_now, volume_per_txn, duration, count_operations, cred_deb,
        frequency_txn, avg_run_bal, due_date, fico_medians, mtx_traffic, mtx_stamina
    ]
'''
def covalent_credibility(txn, balances, feedback, weights, params):

    kyc, feedback = credibility_kyc(
        balances,
        txn, 
        feedback
        )

    inception, feedback = credibility_oldest_txn(
        txn, 
        feedback, 
        params[9],
        params[3]
        )

    a = list(weights.values())[:2]
    b = [kyc, inception]

    score = dot_product(a, b)

    return score, feedback


def covalent_wealth(txn, balances, feedback, weights, params, erc_rank):

    capital_now, feedback = wealth_capital_now(
        balances, 
        feedback, 
        params[9],
        params[1]
        )

    capital_now_adj, feedback = wealth_capital_now_adjusted(
        balances, 
        feedback,
        erc_rank,
        params[9],
        params[1]
        )

    transactional_volume, feedback = wealth_volume_per_txn(
        txn, 
        feedback,
        params[9],
        params[2]
        )

    a = list(weights.values())[2:5]
    b = [capital_now, capital_now_adj, transactional_volume]

    score = dot_product(a, b)

    return score, feedback


def covalent_traffic(txn, portfolio, feedback, weights, params, erc_rank):

    credit, feedback = traffic_cred_deb(
        txn, 
        feedback, 
        'credit',
        params[4],
        params[5],
        params[10]
        )

    debit, feedback = traffic_cred_deb(
        txn, 
        feedback, 
        'debit',
        params[4],
        params[5],
        params[10]
        )

    frequency, feedback = traffic_frequency(
        txn, 
        feedback,
        params[9],
        params[6]
        )

    dust, feedback = traffic_dustiness(
        txn, 
        feedback,
        params[9]
        )

    run_balance, feedback = traffic_running_balance(
        portfolio, 
        feedback,
        params[9],
        params[7],
        erc_rank
        )

    a = list(weights.values())[5:10]
    b = [credit, debit, frequency, dust, run_balance]

    score = dot_product(a, b)

    return score, feedback


def covalent_stamina(txn, balances, portfolio, feedback, weights, params, erc_rank):

    coins, feedback = stamina_coins_count(
        balances, 
        feedback, 
        params[0],
        params[1],
        params[11],
        erc_rank
        )

    methods, feedback = stamina_methods_count(
        txn,
        feedback,
        params[0],
        params[1],
        params[11]
        )

    dexterity, feedback = stamina_dexterity(
        portfolio, 
        feedback,
        params[0],
        params[1],
        params[11]
        )

    feedback = stamina_loan_duedate(
        txn,
        feedback,
        params[8]
        )

    a = list(weights.values())[10:]
    b = [coins, methods, dexterity]

    score = dot_product(a, b)

    return score, feedback