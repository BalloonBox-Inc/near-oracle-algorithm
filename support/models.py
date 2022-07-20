from support.metrics_plaid import *
from support.metrics_coinbase import *
from support.metrics_covalent import *
from support.helper import *


# -------------------------------------------------------------------------- #
#                                Plaid Model                                 #
# -------------------------------------------------------------------------- #


def plaid_credit(acc, txn, cred, feedback, weights, params):

    limit, feedback = credit_limit(txn, cred, feedback, params)
    util_ratio, feedback = credit_util_ratio(acc, txn, feedback, params)
    interest, feedback = credit_interest(acc, txn, feedback, params)
    length, feedback = credit_length(acc, txn, feedback, params)
    livelihood, feedback = credit_livelihood(acc, txn, feedback, params)

    a = list(weights.values())[:5]
    b = [limit, util_ratio, interest, length, livelihood]

    score = dot_product(a, b)

    return score, feedback


def plaid_velocity(acc, txn, feedback, weights, params):

    withdrawals, feedback = velocity_withdrawals(txn, feedback, params)
    deposits, feedback = velocity_deposits(txn, feedback, params)
    net_flow, feedback = velocity_month_net_flow(acc, txn, feedback, params)
    txn_count, feedback = velocity_month_txn_count(acc, txn, feedback, params)
    slope, feedback = velocity_slope(acc, txn, feedback, params)

    a = list(weights.values())[5:10]
    b = [withdrawals, deposits, net_flow, txn_count, slope]

    score = dot_product(a, b)

    return score, feedback


def plaid_stability(acc, txn, dep, n_dep, feedback, weights, params):

    balance, feedback = stability_tot_balance_now(dep, n_dep, feedback, params)
    feedback = stability_loan_duedate(txn, feedback, params)
    run_balance, feedback = stability_min_running_balance(acc, txn, feedback, params)

    a = list(weights.values())[10:12]
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def plaid_diversity(acc, txn, feedback, weights, params):

    acc_count, feedback = diversity_acc_count(acc, txn, feedback, params)
    profile, feedback = diversity_profile(acc, feedback, params)

    a = list(weights.values())[12:]
    b = [acc_count, profile]

    score = dot_product(a, b)

    return score, feedback


# -------------------------------------------------------------------------- #
#                               Coinbase Model                               #
# -------------------------------------------------------------------------- #


def coinbase_kyc(acc, txn, feedback):

    score, feedback = kyc(acc, txn, feedback)

    return score, feedback


def coinbase_history(acc, feedback, params):

    score, feedback = history_acc_longevity(acc, feedback, params)

    return score, feedback


def coinbase_liquidity(acc, txn, feedback, weights, params):

    balance, feedback = liquidity_tot_balance_now(acc, feedback, params)
    feedback = liquidity_loan_duedate(txn, feedback, params)
    run_balance, feedback = liquidity_avg_running_balance(acc, txn, feedback, params)

    a = list(weights.values())[:2]
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def coinbase_activity(acc, txn, feedback, weights, params):

    credit_volume, feedback = activity_tot_volume_tot_count(
        txn, "credit", feedback, params
    )
    debit_volume, feedback = activity_tot_volume_tot_count(
        txn, "debit", feedback, params
    )
    credit_consistency, feedback = activity_consistency(txn, "credit", feedback, params)
    debit_consistency, feedback = activity_consistency(txn, "debit", feedback, params)
    inception, feedback = activity_profit_since_inception(acc, txn, feedback, params)

    a = list(weights.values())[2:]
    b = [credit_volume, debit_volume, credit_consistency, debit_consistency, inception]

    score = dot_product(a, b)

    return score, feedback


# -------------------------------------------------------------------------- #
#                               Covalent Model                               #
# -------------------------------------------------------------------------- #


def covalent_credibility(txn, balances, portfolio, feedback, weights, params):

    feedback = fetch_covalent(txn, balances, portfolio, feedback)

    kyc, feedback = credibility_kyc(txn, balances, feedback)

    inception, feedback = credibility_oldest_txn(
        txn, feedback, params
    )

    a = list(weights.values())[:2]
    b = [kyc, inception]

    score = dot_product(a, b)

    return score, feedback


def covalent_wealth(txn, balances, feedback, weights, params, erc_rank):

    capital_now, feedback = wealth_capital_now(
        balances, feedback, params
    )

    capital_now_adj, feedback = wealth_capital_now_adjusted(
        balances, feedback, erc_rank, params
    )

    volume_per_txn, feedback = wealth_volume_per_txn(
        txn, feedback, params
    )

    a = list(weights.values())[2:5]
    b = [capital_now, capital_now_adj, volume_per_txn]

    score = dot_product(a, b)

    return score, feedback


def covalent_traffic(txn, portfolio, feedback, weights, params, erc_rank):

    credit, feedback = traffic_cred_deb(
        txn,
        feedback,
        "credit",
        params
    )

    debit, feedback = traffic_cred_deb(
        txn,
        feedback,
        "debit",
        params
    )

    dust, feedback = traffic_dustiness(txn, feedback, params)

    run_balance, feedback = traffic_running_balance(
        portfolio, feedback, params, erc_rank
    )

    frequency, feedback = traffic_frequency(
        txn, feedback, params
    )

    a = list(weights.values())[5:10]
    b = [credit, debit, frequency, dust, run_balance]

    score = dot_product(a, b)

    return score, feedback


def covalent_stamina(txn, balances, portfolio, feedback, weights, params, erc_rank):

    methods, feedback = stamina_methods_count(
        txn,
        feedback,
        params
    )

    coins, feedback = stamina_coins_count(
        balances,
        feedback,
        params,
        erc_rank
    )

    dexterity, feedback = stamina_dexterity(
        portfolio,
        feedback,
        params
    )

    feedback = stamina_loan_duedate(txn, feedback, params)

    a = list(weights.values())[10:]
    b = [coins, methods, dexterity]

    score = dot_product(a, b)

    return score, feedback
