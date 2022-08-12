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
    try:
        if metadata['credit_card']:
            # read metadata
            d = metadata['credit_card']['general']
            acc_count = d['accounts']['total_count']
            txn_avg_count = d['transactions']['avg_monthly_count']
            txn_timespan = d['transactions']['timespan']
            bal_limit = sum(d['balances']['limit'])
            limit_usage = [1 - (high - limit)/limit for high, limit in zip(
                d['balances']['high_balance'], d['balances']['limit']) if high > limit]
            if limit_usage:
                limit_usage = [n if n > 0 else 0 for n in limit_usage]
                limit_usage = stt.mean(limit_usage)
            else:
                limit_usage = 1  # never went over limit

            du = metadata['credit_card']['util_ratio']
            util_count = du['general']['month_count']
            util_avg = du['general']['avg_monthly_value']

            dup = du['period']
            util_values = list({k: v for k, v in dup.items() if k <= period}.values())
            util_values = [n if n > 0.3 else 0 for n in util_values]
            util_weights = cum_halves_list(0.25, len(util_values))
            cum_util_ratio = [w/v for v, w in zip(util_values, util_weights) if v > 0]
            if cum_util_ratio:
                cum_util_ratio = 1 - stt.mean([n for n in cum_util_ratio if n < 1])
            else:
                cum_util_ratio = 1  # never used more than 30% of limit

            dl = metadata['credit_card']['late_payment']
            late_pymt_count = dl['general']['total_count']
            late_pymt_mcount = dl['general']['month_count']
            late_pymt_freq = late_pymt_count / late_pymt_mcount

            dlp = dl['period']
            late_pymt_values = list({k: v for k, v in dlp.items() if k <= period}.values())
            late_pymt_weights = cum_halves_list(0.33, len(late_pymt_values))
            late_payment = 1 - sum([w/v for v, w in zip(late_pymt_values, late_pymt_weights) if v > 0])

            # read params
            w = np.digitize(acc_count, params['count_zero'], right=True)
            x = np.digitize(txn_avg_count, params['count_lively'], right=True)
            y = np.digitize(txn_timespan, params['duration'], right=True)
            z = np.digitize(bal_limit, params['volume_credit'], right=True)

            p = np.digitize(util_count*30, params['duration'], right=True)
            q = np.digitize(util_avg, params['credit_util_pct'], right=True)
            r = np.digitize(late_pymt_freq, params['frequency_interest'], right=True)

            # 1. limit
            score.append(limit_usage)
            score.append(params['activity_vol_mtx'][y][z])

            # 2. length
            score.append(params['fico_medians'][y])

            # 3. livelihood
            score.append(params['fico_medians'][x])

            # 4. util ratio
            score.append(params['activity_cns_mtx'][p][q])
            score.append(cum_util_ratio)

            # 5. interest
            score.append(params['fico_medians'][r])
            score.append(late_payment)

            # credit mix
            scorex = params['credit_mix_mtx'][w][y]  # why not using it?

            # update feedback
            feedback['credit']['credit_cards'] = acc_count
            feedback['credit']['avg_count_monthly_txn'] = round(txn_avg_count, 0)
            feedback['credit']['credit_duration_days'] = txn_timespan
            feedback['credit']['credit_limit'] = bal_limit
            feedback['credit']['utilization_ratio'] = round(util_avg, 2)
            feedback['credit']['count_charged_interest'] = round(late_pymt_count, 0)

        else:
            raise Exception('no credit card')

    except Exception as e:
        feedback['credit']['error'] = str(e)

    finally:
        num, size = 5, len(score)
        if size < num:
            score = fill_list(score, num, size)
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
    try:
        if metadata['checking']:
            # read metadata
            d = metadata['checking']['general']
            txn_avg_count = d['transactions']['avg_monthly_count']
            monthly_count = d['balances']['monthly']['total_count']
            overdraft_count = d['balances']['monthly']['overdraft_count']
            monthly_balance = d['balances']['monthly']['balance']

            di = metadata['checking']['income']
            income_avg_count = di['payroll']['avg_monthly_count']
            income_avg_value = di['payroll']['avg_monthly_value']

            de = metadata['checking']['expenses']
            keys = list(de.keys())
            expenses_avg_count = sum([de[k]['avg_monthly_count'] for k in keys])
            expenses_avg_value = sum([de[k]['avg_monthly_value'] for k in keys])

            positives = [n for n in monthly_balance if n >= 0]
            negatives = [n for n in monthly_balance if n < 0]

            direction1 = (monthly_count - overdraft_count) / overdraft_count
            magnitude1 = abs(sum(positives) / sum(negatives))
            if direction1 < 1:
                magnitude1 = magnitude1 * -1

            magnitude2 = stt.mean([abs(n) for n in [income_avg_value, expenses_avg_value]])
            if negatives:
                direction2 = direction1
            else:
                direction2 = 10

            # read params
            w = np.digitize(income_avg_count, params['count_zero'], right=True)
            x = np.digitize(income_avg_value, params['volume_deposit'], right=True)
            y = np.digitize(expenses_avg_count, params['count_zero'], right=True)
            z = np.digitize(expenses_avg_value, params['volume_withdraw'], right=True)

            p = np.digitize(direction2, params['flow_ratio'], right=True)
            q = np.digitize(magnitude2, params['volume_flow'], right=True)
            t = np.digitize(txn_avg_count, params['count_txn'], right=True)

            # 1. deposits
            score.append(params['diversity_velo_mtx'][w][x])

            # 2. withdrawals
            score.append(params['diversity_velo_mtx'][y][z])

            # 3. net_flow
            score.append(params['activity_vol_mtx'][p][q])

            # 4. slope
            if monthly_count >= 10 or overdraft_count == 0:
                a, b = np.polyfit(range(monthly_count), monthly_balance, 1)
                r = np.digitize(a, params['slope_lr'], right=True)
                feedback['velocity']['slope'] = round(a, 2)
                slope = params['fico_medians'][r]
            else:
                r = np.digitize(direction1, params['slope'], right=True)
                s = np.digitize(magnitude1, params['slope'], right=True)
                feedback['velocity']['monthly_flow'] = round(magnitude1, 2)
                slope = params['activity_vol_mtx'].T[r][s]

            score.append(slope)

            # 5. txn_count
            score.append(params['fico_medians'][t])

            # update feedback
            feedback['velocity']['deposits'] = round(income_avg_count, 0)
            feedback['velocity']['deposits_volume'] = round(income_avg_value, 0)
            feedback['velocity']['withdrawals'] = round(expenses_avg_count, 0)
            feedback['velocity']['withdrawals_volume'] = round(expenses_avg_value, 0)
            feedback['velocity']['avg_net_flow'] = round(magnitude2, 2)
            feedback['velocity']['count_monthly_txn'] = round(txn_avg_count, 0)

        else:
            raise Exception('no checking account')

    except Exception as e:
        feedback['velocity']['error'] = str(e)

    finally:
        num, size = 5, len(score)
        if size < num:
            score = fill_list(score, num, size)
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
    try:
        # read metadata
        keys = list(metadata.keys())
        bal_total = [metadata[k]['general']['balances']['current'] for k in keys if metadata[k]['general']]
        bal_total = sum(flatten_list(bal_total))
        txn_timespan = metadata['checking']['general']['transactions']['timespan']
        run_balance = metadata['checking']['general']['balances']['running_balance']
        run_balance_overdraft = len([n for n in run_balance if n < 0])
        run_bal_count = len(run_balance)
        run_bal_weights = np.linspace(0.01, 1, run_bal_count).tolist()
        run_bal_volume = sum([x * w for x, w in zip(run_balance, reversed(run_bal_weights))]) / sum(run_bal_weights)

        # read params
        w = np.digitize(bal_total, params['volume_balance'], right=True)
        x = np.digitize(txn_timespan, params['duration'], right=True)
        y = np.digitize(run_bal_volume, params['volume_min'], right=True)

        # 1. balance
        score.append(params['fico_medians'][w])

        # 2. running balance
        score.append(round(params['activity_cns_mtx'][x][y] - 0.025 * run_balance_overdraft, 2))

        # update feedback
        feedback['stability']['cumulative_current_balance'] = bal_total
        feedback['stability']['min_running_balance'] = round(run_bal_volume, 2)
        feedback['stability']['min_running_timeframe'] = txn_timespan

    except Exception as e:
        feedback['stability']['error'] = str(e)

    finally:
        num, size = 2, len(score)
        if size < num:
            score = fill_list(score, num, size)
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
    try:
        # read metadata
        keys = list(metadata.keys())
        acc_count = sum([metadata[k]['general']['accounts']['total_count'] for k in keys if metadata[k]['general']])
        txn_timespan = max([metadata[k]['general']['transactions']['timespan']
                            for k in keys if metadata[k]['general']])
        txn_mtimespan = int(txn_timespan / 30)

        bal_savings, bal_invest = 0, 0

        if metadata['savings']['general']:
            bal_savings = sum(metadata['savings']['general']['balances']['current'])

        if metadata['checking']['investments']['earnings']:
            bal_invest = metadata['checking']['investments']['earnings']['total_value']

        balance = bal_savings + bal_invest

        # read params
        w = np.digitize(acc_count, [i + 2 for i in params['count_zero']], right=False)
        x = np.digitize(txn_timespan, params['duration'], right=True)
        y = np.digitize(txn_mtimespan, params['due_date'], right=True)
        z = np.digitize(balance, params['volume_invest'], right=True)

        # account
        score.append(params['diversity_velo_mtx'][w][x])

        # profile
        score.append(params['fico_medians'][z])

        # update feedback
        feedback['diversity']['bank_accounts'] = acc_count
        feedback['stability']['loan_duedate'] = np.append(params['due_date'], 6)[y]

        if not balance:
            raise Exception('no savings or investment accounts')

    except Exception as e:
        feedback['diversity']['error'] = str(e)

    finally:
        num, size = 2, len(score)
        if size < num:
            score = fill_list(score, num, size)
        print(f'\033[36m  -> Diversity:\t{score}\033[0m')
        return score, feedback
