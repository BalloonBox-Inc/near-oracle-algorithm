from support.assessment import *
from datetime import timedelta
from datetime import datetime
import pandas as pd
import numpy as np

NOW = datetime.now().date()


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #


def dynamic_select(acc, txn, acc_name, feedback):
    '''
    Description:
        dynamically pick the best credit account,
        i.e. the account that performs best in 2 out of these 3 categories:
        highest credit limit / largest txn count / longest txn history

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        acc_name (str): acccepts 'credit' or 'checking'
        feedback (dict): feedback describing the score

    Returns:
        best (str or dict): Plaid account_id of best credit account
    '''
    try:
        info = list()
        matrix = []
        for a in acc:
            if (acc_name in '{1}{0}{2}'.format('_', str(a['type']), str(a['subtype'])).lower()):

                id = a['account_id']

                type = '{1}{0}{2}{0}{3}'.format('_', str(a['type']), str(a['subtype']), str(a['official_name'])).lower()

                limit = int(a['balances']['limit'] or 0)
                transat = [t for t in txn if t['account_id'] == id]
                txn_count = len(transat)

                if len(transat) != 0:
                    length = (NOW - transat[-1]['date']).days
                else:
                    length = 0
                info.append([id, type, limit, txn_count, length])
                matrix.append([limit, txn_count, length])

        if len(info) != 0:
            # Build a matrix where each column is a different account.
            # Choose the one performing best among the 3 categories
            m = np.array(matrix).T
            m[0] = m[0] * 1  # assign 1pt to credit limit
            m[1] = m[1] * 10  # assign 10pt to txn count
            m[2] = m[2] * 3  # assign 3pt to account length
            cols = [sum(m[:, i]) for i in range(m.shape[1])]
            index_best_acc = cols.index(max(cols))
            best = {'id': info[index_best_acc][0], 'limit': info[index_best_acc][2]}
        else:
            best = {'id': 'inexistent', 'limit': 0}

    except Exception as e:
        feedback['fetch'][dynamic_select.__name__] = str(e)
        best = {'id': 'inexistent', 'limit': 0}

    finally:
        return best


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
# @evaluate_function
def credit_mix(metadata, feedback, params):
    '''
    Description:
        A score based on user's credit accounts composition and status

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): gained based on number of credit accounts owned and duration
        feedback (dict): score feedback
    '''

    try:
        if metadata['credit_card']:
            count = metadata['credit_card']['general']['accounts']['total_count']
            timespan = metadata['credit_card']['general']['transactions']['timespan']

            m = np.digitize(count, params['count_zero'], right=True)
            n = np.digitize(timespan, params['duration'], right=True)
            score = params['credit_mix_mtx'][m][n]

            feedback['credit']['credit_cards'] = count
        else:
            raise Exception('no credit card')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def credit_limit(metadata, feedback, params):
    '''
    Description:
        A score for the cumulative credit limit of a user across ALL of his credit accounts

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): gained based on the cumulative credit limit across all credit accounts
        feedback (dict): score feedback
    '''

    try:
        if metadata['credit_card']:
            timespan = metadata['credit_card']['general']['transactions']['timespan']
            credit_lim = sum(metadata['credit_card']['general']['balances']['limit'])

            m = np.digitize(timespan, params['duration'], right=True)
            n = np.digitize(credit_lim, params['volume_credit'], right=True)
            score = params['activity_vol_mtx'][m][n]

            feedback['credit']['credit_limit'] = credit_lim

        else:
            raise Exception('no credit limit')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def credit_util_ratio(acc, txn, feedback, params):
    '''
    Description:
        A score reflective of the user's credit utilization ratio, that is credit_used/credit_limit

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score for avg percent of credit limit used
        feedback (dict): score feedback
    '''
    try:
        # Dynamically select best credit account
        dynamic = dynamic_select(acc, txn, 'credit', feedback)

        if dynamic['id'] == 'inexistent' or dynamic['limit'] == 0:
            score = 0

        else:
            id = dynamic['id']
            limit = dynamic['limit']

            # Keep ony transactions in best credit account
            transat = [x for x in txn if x['account_id'] == id]

            if transat:
                dates = list()
                amounts = list()
                for t in transat:
                    dates.append(t['date'])
                    amounts.append(t['amount'])
                df = pd.DataFrame(data={'amounts': amounts}, index=pd.DatetimeIndex(dates))

                # Bin by month credit card 'purchases' and 'paybacks'
                util = df.groupby(pd.Grouper(freq='M'))['amounts'].agg(
                    [('payback', lambda x: x[x < 0].sum()), ('purchases', lambda x: x[x > 0].sum()), ])
                util['cred_util'] = [x / limit for x in util['purchases']]

                # Exclude current month
                if util.iloc[-1, ].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
                    util = util[:-1]

                avg_util = np.mean(util['cred_util'])
                m = np.digitize(len(util) * 30, params['duration'], right=True)
                n = np.digitize(avg_util, params['credit_util_pct'], right=True)
                score = params['activity_cns_mtx'][m][n]

                feedback['credit']['utilization_ratio'] = round(avg_util, 2)

            else:
                raise Exception('no credit history')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def credit_interest(acc, txn, feedback, params):
    '''
    Description:
        returns score based on number of times user was charged
        credit card interest fees in past 24 months

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): gained based on interest charged
        feedback (dict): feedback describing the score
    '''
    try:
        id = dynamic_select(acc, txn, 'credit', feedback)['id']

        if id == 'inexistent':
            score = 0

        else:
            alltxn = [t for t in txn if t['account_id'] == id]

            interests = list()

            if alltxn:
                length = min(24, round((NOW - alltxn[-1]['date']).days / 30, 0))
                for t in alltxn:

                    # keep only txn of type 'interest on credit card'
                    if 'Interest Charged' in t['category']:
                        date = t['date']

                        # keep only txn of last 24 months
                        if date > NOW - timedelta(days=2 * 365):
                            interests.append(t)

                frequency = len(interests) / length
                score = params['fico_medians'][np.digitize(frequency, params['frequency_interest'], right=True)]

                feedback['credit']['count_charged_interest'] = round(frequency, 0)

            else:
                raise Exception('no credit interest')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def credit_length(metadata, feedback, params):
    '''
    Description:
        returns score based on length of user's best credit account

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): gained because of credit account duration
        feedback (dict): feedback describing the score
    '''
    try:
        if metadata['credit_card']:
            timespan = metadata['credit_card']['general']['transactions']['timespan']

            score = params['fico_medians'][np.digitize(timespan, params['duration'], right=True)]

            feedback['credit']['credit_duration_days'] = timespan

        else:
            raise Exception('no credit length')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def credit_livelihood(metadata, feedback, params):
    '''
    Description:
        returns score quantifying the avg monthly txn count for your best credit account

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): based on avg monthly txn count
        feedback (dict): feedback describing the score
    '''
    try:
        if metadata['credit_card']:
            mean = metadata['credit_card']['general']['transactions']['avg_monthly_count']

            score = params['fico_medians'][np.digitize(mean, params['count_lively'], right=True)]

            feedback['credit']['avg_count_monthly_txn'] = round(mean, 0)

        else:
            raise Exception('no credit transactions')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- #


# @evaluate_function
def velocity_withdrawals(txn, feedback, params):
    '''
    Description:
        returns score based on count and volumne of monthly automated withdrawals

    Parameters:
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score associated with reccurring monthly withdrawals
        feedback (dict): feedback describing the score
    '''
    try:
        withdraw = [
            ['Service', 'Subscription'],
            ['Service', 'Financial', 'Loans and Mortgages'],
            ['Service', 'Insurance'],
            ['Payment', 'Rent'],
        ]
        dates = list()
        amounts = list()

        for t in txn:
            if t['category'] in withdraw and t['amount'] > 15:
                dates.append(t['date'])
                amounts.append(abs(t['amount']))

        df = pd.DataFrame(data={'amounts': amounts}, index=pd.DatetimeIndex(dates))

        if len(df.index) > 0:
            how_many = np.mean(
                df.groupby(pd.Grouper(freq='M')).count().iloc[:, 0].tolist()
            )
            if how_many > 0:
                volume = np.mean(
                    df.groupby(pd.Grouper(freq='M')).sum().iloc[:, 0].tolist()
                )

                m = np.digitize(how_many, params['count_zero'], right=True)
                n = np.digitize(volume, params['volume_withdraw'], right=True)
                score = params['diversity_velo_mtx'][m][n]

                feedback['velocity']['withdrawals'] = round(how_many, 0)
                feedback['velocity']['withdrawals_volume'] = round(volume, 0)

        else:
            raise Exception('no withdrawals')

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def velocity_deposits(metadata, feedback, params):
    '''
    Description:
        returns score based on count and volumne of monthly automated deposits

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score associated with direct deposits
        feedback (dict): feedback describing the score
    '''
    try:
        if metadata['checking']:
            count = metadata['checking']['income']['payroll']['avg_monthly_count']
            volume = metadata['checking']['income']['payroll']['avg_monthly_value']

            m = np.digitize(count, params['count_zero'], right=True)
            n = np.digitize(volume, params['volume_deposit'], right=True)
            score = params['diversity_velo_mtx'][m][n]

            feedback['velocity']['deposits'] = round(count, 0)
            feedback['velocity']['deposits_volume'] = round(volume, 0)

        else:
            raise Exception('no deposits')

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def velocity_month_net_flow(acc, txn, feedback, params):
    '''
    Description:
        returns score for monthly net flow

    Parameters:
        acc (list): Plaid 'Accounts' product
        txn (list): Plaid 'Transactions' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score associated with monthly new flow
        feedback (dict): feedback describing the score
    '''
    try:
        flow = flows(acc, txn, 12, feedback)

        # Calculate magnitude of flow (how much is flowing monthly?)
        cum_flow = [abs(x) for x in flow['amounts'].tolist()]
        magnitude = np.mean(cum_flow)

        # Calculate direction of flow (is money coming in or going out?)
        neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
        pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))

        if neg:
            direction = len(pos) / len(neg)  # output in range [0, ...)
        else:
            direction = 10  # 10 is an arbitrality chosen large positive integer

        # Calculate score
        m = np.digitize(direction, params['flow_ratio'], right=True)
        n = np.digitize(magnitude, params['volume_flow'], right=True)
        score = params['activity_vol_mtx'][m][n]

        feedback['velocity']['avg_net_flow'] = round(magnitude, 2)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def velocity_month_txn_count(metadata, feedback, params):
    '''
    Description:
        returns score based on count of mounthly transactions

    Parameters:
        metadata (dict): Plaid accounts and transactions overview
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): the larger the monthly count the larger the score
        feedback (dict): feedback describing the score
    '''
    try:
        if metadata['checking']:
            count = metadata['checking']['general']['transactions']['avg_monthly_count']

        score = params['fico_medians'][np.digitize(count, params['count_txn'], right=True)]

        feedback['velocity']['count_monthly_txn'] = round(count, 0)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
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

            score = params['fico_medians'][
                np.digitize(a, params['slope_lr'], right=True)
            ]

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


# @evaluate_function
def stability_tot_balance_now(depository, non_depository, feedback, params):
    '''
    Description:
        A score based on total balance now across ALL accounts owned by the user

    Parameters:
        depository (list): Plaid 'Accounts' product - depository accounts only
        non_depository (list): Plaid 'Accounts' product - except depository accounts
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): cumulative current balance
        feedback (dict): score feedback
    '''
    try:
        x = sum([int(d['balances']['current']) if d['balances']['current'] else 0 for d in depository])
        y = sum([int(d['balances']['available']) if d['balances']['available'] else 0 for d in non_depository])
        balance = x + y

        if balance > 0:
            score = params['fico_medians'][
                np.digitize(balance, params['volume_balance'], right=True)
            ]
            feedback['stability']['cumulative_current_balance'] = balance
            stability_tot_balance_now.balance = balance

        else:
            raise Exception('no balance')

    except Exception as e:
        score = 0
        feedback['stability']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def stability_loan_duedate(timespan, feedback, params):
    '''
    Description:
        returns how many months it'll take the user to pay back their loan

    Parameters:
        timespan (int): timespan since first transaction
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        feedback (dict): score feedback with a new key-value pair
        'loan_duedate':float (# of months in range [3,6])
    '''

    try:
        # Loan duedate is equal to the month of txn history there are
        due = np.digitize(int(timespan / 30), params['due_date'], right=True)
        how_many_months = np.append(params['due_date'], 6)

        feedback['stability']['loan_duedate'] = how_many_months[due]

    except Exception as e:
        feedback['stability']['error'] = str(e)

    finally:
        return feedback


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


# @evaluate_function
def diversity_acc_count(count, timespan, feedback, params):
    '''
    Description:
        A score based on count of accounts owned by the user and account duration

    Parameters:
        count (int): active accounts count
        timespan (int): timespan since first transaction
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): score for accounts count
        feedback (dict): score feedback
    '''

    try:
        m = np.digitize(count, [i + 2 for i in params['count_zero']], right=False)
        n = np.digitize(timespan, params['duration'], right=True)
        score = params['diversity_velo_mtx'][m][n]

        feedback['diversity']['bank_accounts'] = count

    except Exception as e:
        score = 0
        feedback['diversity']['error'] = str(e)

    finally:
        return score, feedback


# @evaluate_function
def diversity_profile(acc, feedback, params):
    '''
    Description:
        A score for number of saving and investment accounts owned

    Parameters:
        acc (list): Plaid 'Accounts' product
        feedback (dict): score feedback
        params (dict): model parameters, i.e. coefficients

    Returns:
        score (float): points scored for accounts owned
        feedback (dict): score feedback
    '''

    try:
        acc = [x for x in acc if x['type'] == 'loan' or int(
            x['balances']['current'] or 0) != 0]  # exclude $0 balance accounts

        balance = 0
        for a in acc:
            type = '{}_{}'.format(a['type'], str(a['subtype']))

            # Consider savings, hda, cd, money mart, paypal, prepaid, cash management, edt accounts
            if (type.split('_')[0] == 'depository') & (type.split('_')[1] != 'checking'):
                balance += int(a['balances']['current'] or 0)

            # Consider ANY type of investment account
            if type.split('_')[0] == 'investment':
                balance += int(a['balances']['current'] or 0)

        if balance != 0:
            score = params['fico_medians'][np.digitize(balance, params['volume_invest'], right=True)]

        else:
            raise Exception('no investing nor savings accounts')

    except Exception as e:
        score = 0
        feedback['diversity']['error'] = str(e)

    finally:
        return score, feedback
