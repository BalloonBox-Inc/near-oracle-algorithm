from support.assessment import *
from helpers.helper import *
import statistics as stt
import numpy as np


def plaid_kyc(acc, txn):
    '''
    Description:
        returns True if the oracle believes this is a legitimate user
        with some credible history. Returns False otherwise

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product

    Returns:
        (boolean): True if user is legitimate and False otherwise
    '''
    try:
        # user is verified iff acc and txn data exist,
        # iff the account has been active for > 90 days
        # iff their cumulative balance across all account is > $500
        from datetime import datetime
        now = datetime.now().date()  # remove it later, fetch from metadata
        if txn and acc and (now - txn[-1]['date']).days and sum([a['balances']['current'] for a in acc if a['balances']['current']]):
            return True
        else:
            return False

    except Exception as e:
        return str(e)


# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #


def plaid_credit_metrics(feedback, params, metadata, period):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"credit": {"metrics": {...}}}}}}}]
    '''
    score = []

    if metadata['credit_card']['general']:

        d = metadata['credit_card']['general']
        du = metadata['credit_card']['util_ratio']
        dl = metadata['credit_card']['late_payment']

        feedback['credit']['credit_cards'] = d['accounts']['total_count']

        # 1. limit_usage
        try:
            limit_usage = [1 - (high - limit)/limit for high, limit in zip(
                d['balances']['high_balance'], d['balances']['limit']) if high > limit]

            if limit_usage:
                limit_usage = [n if n > 0 else 0 for n in limit_usage]
                limit_usage = stt.mean(limit_usage)
            else:
                limit_usage = 1  # never went over limit

            score.append(limit_usage)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 2. limit
        # 3. length
        try:
            txn_timespan = d['transactions']['timespan']
            bal_limit = sum(d['balances']['limit'])

            w = np.digitize(txn_timespan, params['duration'], right=True)
            x = np.digitize(bal_limit, params['volume_credit'], right=True)

            score.append(params['activity_vol_mtx'][w][x])
            score.append(params['fico_medians'][w])
            feedback['credit']['credit_duration_days'] = txn_timespan
            feedback['credit']['credit_limit'] = bal_limit

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)
            score.append(0)

        # 4. livelihood
        try:
            txn_avg_count = d['transactions']['avg_monthly_count']

            y = np.digitize(txn_avg_count, params['count_lively'], right=True)

            score.append(params['fico_medians'][y])
            feedback['credit']['avg_count_monthly_txn'] = round(txn_avg_count, 0)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 5. util ratio
        try:
            util_count = du['general']['month_count']
            util_avg = du['general']['avg_monthly_value']

            p = np.digitize(util_count*30, params['duration'], right=True)
            q = np.digitize(util_avg, params['credit_util_pct'], right=True)

            score.append(params['activity_cns_mtx'][p][q])
            feedback['credit']['utilization_ratio'] = round(util_avg, 2)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 6. cum_util_ratio
        try:
            dup = du['period']
            util_values = list({k: v for k, v in dup.items() if k <= period}.values())
            util_values = [n if n > 0.3 else 0 for n in util_values]
            util_weights = cum_halves_list(0.25, len(util_values))
            cum_util_ratio = [w/v for v, w in zip(util_values, util_weights) if v > 0]
            if cum_util_ratio:
                cum_util_ratio = 1 - stt.mean([n for n in cum_util_ratio if n < 1])
            else:
                cum_util_ratio = 1  # never used more than 30% of limit

            score.append(cum_util_ratio)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 7. interest
        try:
            late_pymt_count = dl['general']['total_count']
            late_pymt_mcount = dl['general']['month_count']
            late_pymt_freq = late_pymt_count / late_pymt_mcount

            r = np.digitize(late_pymt_freq, params['frequency_interest'], right=True)

            score.append(params['fico_medians'][r])
            feedback['credit']['count_charged_interest'] = round(late_pymt_count, 0)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 8. late_payment
        try:
            dlp = dl['period']
            late_pymt_values = list({k: v for k, v in dlp.items() if k <= period}.values())
            late_pymt_weights = cum_halves_list(0.33, len(late_pymt_values))
            late_payment = 1 - sum([w/v for v, w in zip(late_pymt_values, late_pymt_weights) if v > 0])

            score.append(late_payment)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

    # fill up score list if size different from metrics count
    metrics, size = 8, len(score)
    if size < metrics:
        score = fill_list(score, metrics, size)
    print(f'\033[36m  -> Credit:\t{score}\033[0m')
    return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- #


def plaid_velocity_metrics(feedback, params, metadata):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"velocity": {"metrics": {...}}}}}}}]
    '''
    score = []

    if metadata['checking']['general']:

        d = metadata['checking']['general']
        di = metadata['checking']['income']
        de = metadata['checking']['expenses']

        # 1. deposits
        try:
            income_avg_count = di['payroll']['avg_monthly_count']
            income_avg_value = di['payroll']['avg_monthly_value']

            w = np.digitize(income_avg_count, params['count_zero'], right=True)
            x = np.digitize(income_avg_value, params['volume_deposit'], right=True)

            score.append(params['diversity_velo_mtx'][w][x])
            feedback['velocity']['deposits'] = round(income_avg_count, 0)
            feedback['velocity']['deposits_volume'] = round(income_avg_value, 0)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 2. withdrawals
        try:
            keys = list(de.keys())
            expenses_avg_count = sum([de[k]['avg_monthly_count'] for k in keys])
            expenses_avg_value = sum([de[k]['avg_monthly_value'] for k in keys])

            y = np.digitize(expenses_avg_count, params['count_zero'], right=True)
            z = np.digitize(expenses_avg_value, params['volume_withdraw'], right=True)

            score.append(params['diversity_velo_mtx'][y][z])
            feedback['velocity']['withdrawals'] = round(expenses_avg_count, 0)
            feedback['velocity']['withdrawals_volume'] = round(expenses_avg_value, 0)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 3. net_flow
        try:
            income_avg_value = di['payroll']['avg_monthly_value']
            expenses_avg_value = sum([de[k]['avg_monthly_value'] for k in list(de.keys())])
            magnitude = stt.mean([abs(n) for n in [income_avg_value, expenses_avg_value]])

            monthly_count = d['balances']['monthly']['total_count']
            overdraft_count = d['balances']['monthly']['overdraft_count']
            monthly_balance = d['balances']['monthly']['balance']
            negatives = [n for n in monthly_balance if n < 0]

            if negatives:
                direction = (monthly_count - overdraft_count) / overdraft_count
            else:
                direction = 10

            p = np.digitize(direction, params['flow_ratio'], right=True)
            q = np.digitize(magnitude, params['volume_flow'], right=True)

            score.append(params['activity_vol_mtx'][p][q])
            feedback['velocity']['avg_net_flow'] = round(magnitude, 2)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 4. slope
        try:
            monthly_count = d['balances']['monthly']['total_count']
            overdraft_count = d['balances']['monthly']['overdraft_count']
            monthly_balance = d['balances']['monthly']['balance']

            positives = [n for n in monthly_balance if n >= 0]
            negatives = [n for n in monthly_balance if n < 0]

            direction = (monthly_count - overdraft_count) / overdraft_count
            magnitude = abs(sum(positives) / sum(negatives))
            if direction < 1:
                magnitude = magnitude * -1

            if monthly_count >= 10 or overdraft_count == 0:
                a, b = np.polyfit(range(monthly_count), monthly_balance, 1)
                r = np.digitize(a, params['slope_lr'], right=True)
                slope = params['fico_medians'][r]
                feedback['velocity']['slope'] = round(a, 2)

            else:
                r = np.digitize(direction, params['slope'], right=True)
                s = np.digitize(magnitude, params['slope'], right=True)
                slope = params['activity_vol_mtx'].T[r][s]
                feedback['velocity']['monthly_flow'] = round(magnitude, 2)

            score.append(slope)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

        # 5. txn_count
        try:
            txn_avg_count = d['transactions']['avg_monthly_count']

            t = np.digitize(txn_avg_count, params['count_txn'], right=True)

            score.append(params['fico_medians'][t])
            feedback['velocity']['count_monthly_txn'] = round(txn_avg_count, 0)

        except Exception as e:
            print(f'\033[33m Warning: {e}\033[0m')
            score.append(0)

    # fill up score list if size different from metrics count
    metrics, size = 5, len(score)
    if size < metrics:
        score = fill_list(score, metrics, size)
    print(f'\033[36m  -> Velocity:\t{score}\033[0m')
    return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #


def plaid_stability_metrics(feedback, params, metadata):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"stability": {"metrics": {...}}}}}}}]
    '''
    score = []

    # 1. balance
    try:
        keys = list(metadata.keys())
        bal_total = [metadata[k]['general']['balances']['current'] for k in keys if metadata[k]['general']]
        bal_total = sum(flatten_list(bal_total))

        w = np.digitize(bal_total, params['volume_balance'], right=True)

        score.append(params['fico_medians'][w])
        feedback['stability']['cumulative_current_balance'] = bal_total

    except Exception as e:
        print(f'\033[33m Warning: {e}\033[0m')
        score.append(0)

    # 2. running balance
    try:
        txn_timespan = metadata['checking']['general']['transactions']['timespan']
        run_balance = metadata['checking']['general']['balances']['running_balance']
        run_balance_overdraft = len([n for n in run_balance if n < 0])
        run_bal_count = len(run_balance)
        run_bal_weights = np.linspace(0.01, 1, run_bal_count).tolist()
        run_bal_volume = sum([x * w for x, w in zip(run_balance, reversed(run_bal_weights))]) / sum(run_bal_weights)

        x = np.digitize(txn_timespan, params['duration'], right=True)
        y = np.digitize(run_bal_volume, params['volume_min'], right=True)

        score.append(round(params['activity_cns_mtx'][x][y] - 0.025 * run_balance_overdraft, 2))
        feedback['stability']['min_running_balance'] = round(run_bal_volume, 2)
        feedback['stability']['min_running_timeframe'] = txn_timespan

    except Exception as e:
        print(f'\033[33m Warning: {e}\033[0m')
        score.append(0)

    # fill up score list if size different from metrics count
    metrics, size = 2, len(score)
    if size < metrics:
        score = fill_list(score, metrics, size)
    print(f'\033[36m  -> Stability:\t{score}\033[0m')
    return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #


def plaid_diversity_metrics(feedback, params, metadata):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"diversity": {"metrics": {...}}}}}}}]
    '''
    score = []

    # 1. account
    try:
        keys = list(metadata.keys())
        acc_count = sum([metadata[k]['general']['accounts']['total_count'] for k in keys if metadata[k]['general']])
        txn_timespan = max([metadata[k]['general']['transactions']['timespan']
                            for k in keys if metadata[k]['general']])
        txn_mtimespan = int(txn_timespan / 30)

        w = np.digitize(acc_count, [i + 2 for i in params['count_zero']], right=False)
        x = np.digitize(txn_timespan, params['duration'], right=True)
        y = np.digitize(txn_mtimespan, params['due_date'], right=True)

        score.append(params['diversity_velo_mtx'][w][x])
        feedback['diversity']['bank_accounts'] = acc_count
        feedback['stability']['loan_duedate'] = np.append(params['due_date'], 6)[y]

    except Exception as e:
        print(f'\033[33m Warning: {e}\033[0m')
        score.append(0)

    # 2 .profile
    try:
        bal_savings, bal_invest = 0, 0

        if metadata['savings']['general']:
            bal_savings = sum(metadata['savings']['general']['balances']['current'])

        if metadata['checking']['investments']['earnings']:
            bal_invest = metadata['checking']['investments']['earnings']['total_value']

        balance = bal_savings + bal_invest

        z = np.digitize(balance, params['volume_invest'], right=True)

        score.append(params['fico_medians'][z])

    except Exception as e:
        print(f'\033[33m Warning: {e}\033[0m')
        score.append(0)

    # fill up score list if size different from metrics count
    metrics, size = 2, len(score)
    if size < metrics:
        score = fill_list(score, metrics, size)
    print(f'\033[36m  -> Diversity:\t{score}\033[0m')
    return score, feedback
