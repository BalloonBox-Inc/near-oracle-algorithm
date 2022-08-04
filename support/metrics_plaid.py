from support.assessment import *
from support.helper import *
import statistics as stt
import numpy as np

from icecream import ic
import pandas as pd
from datetime import datetime
NOW = datetime.now().date()


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #


def flows(acc, txn, how_many_months, feedback):
    '''
    Description:
        returns monthly net flow

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        how_many_month (float): how many months of transaction history are you considering?
        feedback (dict): feedback describing the score

    Returns:
        flow (df): pandas dataframe with amounts for net monthly flow and datetime index
    '''
    try:
        dates = list()
        amounts = list()
        deposit_acc = list()

        # Keep only deposit->checking accounts
        for a in acc:
            type = '{1}{0}{2}'.format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                deposit_acc.append(a['account_id'])

        # Keep only txn in deposit->checking accounts
        transat = [t for t in txn if t['account_id'] in deposit_acc]

        # Keep only income and expense transactions
        for t in transat:
            if not t['category']:
                pass
            else:
                category = t['category']

            # exclude micro txn and exclude internal transfers
            if abs(t['amount']) > 5 and 'internal account transfer' not in category:
                dates.append(t['date'])
                amounts.append(t['amount'])
        df = pd.DataFrame(data={'amounts': amounts}, index=pd.DatetimeIndex(dates))

        # Bin by month
        flow = df.groupby(pd.Grouper(freq='M')).sum()

        # Exclude current month
        if flow.iloc[-1, ].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
            flow = flow[:-1]

        # Keep only past X months. If longer, then crop
        flow.reset_index(drop=True, inplace=True)
        if how_many_months - 1 in flow.index:
            flow = flow[-(how_many_months):]

        return flow

    except Exception as e:
        feedback['fetch'][flows.__name__] = str(e)


def balance_now_checking_only(acc, feedback):
    '''
    Description:
        returns total balance available now in the user's checking accounts

    Parameters:
        acc (list): Plaid 'Accounts' product
        feedback (dict): feedback describing the score

    Returns:
        balance (float): cumulative current balance in checking accounts
    '''
    try:
        balance = 0
        for a in acc:
            type = '{1}{0}{2}'.format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                balance += int(a['balances']['current'] or 0)

        return balance

    except Exception as e:
        feedback['fetch'][balance_now_checking_only.__name__] = str(e)


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
        if txn and acc and (NOW - txn[-1]['date']).days and sum([a['balances']['current'] for a in acc if a['balances']['current']]):
            return True
        else:
            return False

    except Exception as e:
        return str(e)


# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #


def plaid_credit_metrics(feedback, params, metadata, score=[]):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"credit": {"metrics": {...}}}}}}}]
    '''
    try:
        if metadata['credit_card']:
            # read metadata
            d = metadata['credit_card']['general']
            acc_count = d['accounts']['total_count']
            txn_avg_count = d['transactions']['avg_monthly_count']
            txn_timespan = d['transactions']['timespan']
            bal_limit = sum(d['balances']['limit'])  # shouldnt be average?

            du = metadata['credit_card']['util_ratio']
            util_count = du['general']['month_count']
            util_avg = du['general']['avg_monthly_value']

            dl = metadata['credit_card']['late_payment']
            late_pymt_count = dl['general']['total_count']
            late_pymt_mcount = dl['general']['month_count']
            late_pymt_freq = late_pymt_count / late_pymt_mcount

            # read params
            w = np.digitize(acc_count, params['count_zero'], right=True)
            x = np.digitize(txn_avg_count, params['count_lively'], right=True)
            y = np.digitize(txn_timespan, params['duration'], right=True)
            z = np.digitize(bal_limit, params['volume_credit'], right=True)

            p = np.digitize(util_count*30, params['duration'], right=True)
            q = np.digitize(util_avg, params['credit_util_pct'], right=True)
            r = np.digitize(late_pymt_freq, params['frequency_interest'], right=True)

            # 1. limit
            score.append(params['activity_vol_mtx'][y][z])

            # 2. length
            score.append(params['fico_medians'][y])

            # 3. livelihood
            score.append(params['fico_medians'][x])

            # 4. util ratio
            score.append(params['activity_cns_mtx'][p][q])

            # 5. interest
            score.append(params['fico_medians'][r])

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


def plaid_velocity_metrics(feedback, params, metadata, score=[]):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"velocity": {"metrics": {...}}}}}}}]
    '''
    try:
        # ic(metadata)
        if metadata['checking']:
            # read metadata
            d = metadata['checking']['general']
            txn_avg_count = d['transactions']['avg_monthly_count']

            di = metadata['checking']['income']
            income_avg_count = di['payroll']['avg_monthly_count']
            income_avg_value = di['payroll']['avg_monthly_value']

            de = metadata['checking']['expenses']
            keys = list(de.keys())
            expenses_avg_count = sum([de[k]['avg_monthly_count'] for k in keys])
            expenses_avg_value = sum([de[k]['avg_monthly_value'] for k in keys])

            mag1 = stt.mean([abs(n) for n in [income_avg_value, expenses_avg_value]])
            mag2 = 1
            dir = 10  # count pos months / count neg months

            # read params
            w = np.digitize(income_avg_count, params['count_zero'], right=True)
            x = np.digitize(income_avg_value, params['volume_deposit'], right=True)
            y = np.digitize(expenses_avg_count, params['count_zero'], right=True)
            z = np.digitize(expenses_avg_value, params['volume_withdraw'], right=True)

            p = np.digitize(dir, params['flow_ratio'], right=True)
            q = np.digitize(mag1, params['volume_flow'], right=True)
            r = 1
            s = 1

            t = np.digitize(txn_avg_count, params['count_txn'], right=True)

            # 1. deposits
            score.append(params['diversity_velo_mtx'][w][x])

            # 2. withdrawals
            score.append(params['diversity_velo_mtx'][y][z])

            # 3. net_flow
            score.append(params['activity_vol_mtx'][p][q])

            # 4. slope
            score.append(0)

            # 5. txn_count
            score.append(params['fico_medians'][t])

            # update feedback
            feedback['velocity']['deposits'] = round(income_avg_count, 0)
            feedback['velocity']['deposits_volume'] = round(income_avg_value, 0)
            feedback['velocity']['withdrawals'] = round(expenses_avg_count, 0)
            feedback['velocity']['withdrawals_volume'] = round(expenses_avg_value, 0)
            feedback['velocity']['avg_net_flow'] = round(mag1, 2)
            feedback['velocity']['monthly_flow'] = round(mag2, 2)
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


# @evaluate_function
def velocity_slope(acc, txn, feedback, params):
    '''
    Description:
        returns score for the historical behavior of the net monthly flow for past 24 months

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score for flow net behavior over past 24 months
        feedback (dict): feedback describing the score
    '''
    try:
        flow = flows(acc, txn, 24, feedback)

        # If you have > 10 data points OR all net flows are positive, then perform linear regression
        if (
            len(flow) >= 10
            or len(list(filter(lambda x: (x < 0), flow['amounts'].tolist()))) == 0
        ):
            # Perform Linear Regression using numpy.polyfit()
            x = range(len(flow['amounts']))
            y = flow['amounts']
            a, b = np.polyfit(x, y, 1)

            score = params['fico_medians'][np.digitize(a, params['slope_lr'], right=True)]

            feedback['velocity']['slope'] = round(a, 2)

        # If you have < 10 data points, then calculate the score accounting for two ratios
        else:
            # Multiply two ratios by each other
            neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
            pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))
            direction = len(pos) / len(neg)  # output in range [0, 2+]
            magnitude = abs(sum(pos) / sum(neg))  # output in range [0, 2+]
            if direction >= 1:
                pass
            else:
                magnitude = magnitude * -1
            m = np.digitize(direction, params['slope'], right=True)
            n = np.digitize(magnitude, params['slope'], right=True)
            score = params['activity_vol_mtx'].T[m][n]

            feedback['velocity']['monthly_flow'] = round(magnitude, 2)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #


def plaid_stability_metrics(feedback, params, metadata, score=[]):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"stability": {"metrics": {...}}}}}}}]
    '''
    try:
        if not score:
            # read metadata
            keys = list(metadata.keys())
            bal_total = [metadata[k]['general']['balances']['current'] for k in keys if metadata[k]['general']]
            bal_total = sum(flatten_list(bal_total))

            # read params
            w = np.digitize(bal_total, params['volume_balance'], right=True)

            # 1. balance
            score.append(params['fico_medians'][w])

            # 2. running balance
            score.append(0)

            # update feedback
            feedback['stability']['cumulative_current_balance'] = bal_total

        else:
            raise Exception('no ...')

    except Exception as e:
        feedback['stability']['error'] = str(e)

    finally:
        num, size = 2, len(score)
        if size < num:
            score = fill_list(score, num, size)
        print(f'\033[36m  -> Stability:\t{score}\033[0m')
        return score, feedback


# @evaluate_function
def stability_min_running_balance(acc, txn, feedback, params):
    '''
    Description:
        A score based on the average minimum balance maintained for 12 months

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): volume of minimum balance and duration
        feedback (dict): score feedback
    '''

    try:
        # Calculate net flow each month for past 12 months i.e, |income-expenses|
        nets = flows(acc, txn, 12, feedback)['amounts'].tolist()

        # Calculate total current balance now
        balance = balance_now_checking_only(acc, feedback)

        # Subtract net flow from balancenow to calculate the running balance for the past 12 months
        running_balances = [balance + n for n in reversed(nets)]

        # Calculate volume using a weighted average
        weights = np.linspace(
            0.01, 1, len(running_balances)
        ).tolist()  # define your weights
        volume = sum(
            [x * w for x, w in zip(running_balances, reversed(weights))]
        ) / sum(weights)
        length = len(running_balances) * 30

        # Compute the score
        m = np.digitize(length, params['duration'], right=True)
        n = np.digitize(volume, params['volume_min'], right=True)
        # add 0.025 score penalty for each overdrafts
        score = round(
            params['activity_cns_mtx'][m][n]
            - 0.025 * len(list(filter(lambda x: (x < 0), running_balances))),
            2,
        )

        feedback['stability']['min_running_balance'] = round(volume, 2)
        feedback['stability']['min_running_timeframe'] = length

    except Exception as e:
        score = 0
        feedback['stability']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #


def plaid_diversity_metrics(feedback, params, metadata, score=[]):
    '''
    score[list] order must be the same as showed under metrics in the cofig.json file, e.g.
    "data": [{"minimum_requirements": {"plaid": {"scores": {"models": {"diversity": {"metrics": {...}}}}}}}]
    '''
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
