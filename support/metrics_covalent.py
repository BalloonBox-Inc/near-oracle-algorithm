import numpy as np
from datetime import datetime

# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #

# -------------------------------------------------------------------------- #
#                            Metric #1 Credibility                           #
# -------------------------------------------------------------------------- #
def credibility_kyc(balances, txn, feedback):
    '''
    Description:
        checks whether an ETH wallet address has legitimate transactin history and active balances

    Parameters:
        balances (dict): Covalent class A endpoint 'balances_v2'
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback

    Returns:
        score (float): 1 if KYC'ed and 0
        feedback (dict): updated score feedback
    '''
    try:
        # Assign max score as long as the user owns some credible non-zero balance accounts with some transaction history
        if balances and txn:
            score = 1
            feedback['credibility']['verified'] = True
        else:
            score = 0
            feedback['credibility']['verified'] = False

    except Exception as e:
        score = 0
        feedback['credibility']['error'] = str(e)

    finally:
        return score, feedback


def credibility_oldest_txn(txn, feedback, fico_medians, duration):
    '''
    Description:
        returns score based on total volume of token owned (USD) now

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        fico_medians (array): score bins
        duration (array): account duration bins (days)

    Returns:
        score (float): points scored for longevity of ETH wallet address
        feedback (dict): updated score feedback
    '''
    try:
        oldest = datetime.strptime(txn['items'][-1]['block_signed_at'].split('T')[0], '%Y-%m-%d').date()
        how_long = (now - oldest).days

        score = fico_medians[np.digitize(how_long, duration, right=True)]
        feedback['credibility']['longevity(days)'] = how_long

    except Exception as e:
        score = 0
        feedback['credibility']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                              Metric #2 Wealth                              #
# -------------------------------------------------------------------------- #
def wealth_capital_now(balances, feedback, fico_medians, volume_now):
    '''
    Description:
        returns score based on total volume of token owned (USD) now

    Parameters:
        balances (dict): Covalent class A endpoint 'balances_v2'
        feedback (dict): score feedback
        fico_medians (array): score bins
        volume_now (array): bins for the total token volume owned now

    Returns:
        score (float): points for cumulative balance now
        feedback (dict): updated score feedback
    '''
    try:
        if balances['quote_currency'] == 'USD':
            total = 0
            for b in balances['items']:
                partial = b['quote']
                total += partial

            score = fico_medians[np.digitize(total, volume_now, right=True)]
            feedback['wealth']['cum_balance_now'] = round(total, 2)
        else:
            raise Exception('quote_currency should be USD')

    except Exception as e:
        score = 0
        feedback['wealth']['error'] = str(e)

    finally:
        return score, feedback


def wealth_volume_per_txn(txn, feedback, fico_medians, volume_per_txn):
    '''
    Description:
       returns a score for the avg volume per transaction

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        fico_medians (array): score bins
        volume_per_txn (array): bins for the average volume traded on each transaction

    Returns:
        score (float): volume for each performed transactions
        feedback (dict): updated score feedback
    '''
    try:
        volume = 0
        for t in txn['items']:
            volume += t['value_quote']
        volume_avg = volume/len(txn['items'])

        score = fico_medians[np.digitize(volume_avg, volume_per_txn, right=True)]
        feedback['wealth']['avg_volume_per_txn'] = round(volume_avg, 2)

    except Exception as e:
        score = 0
        feedback['wealth']['error'] = str(e)

    finally:
        return score, feedback
    

# -------------------------------------------------------------------------- #
#                             Metric #3 Traffic                              #
# -------------------------------------------------------------------------- #


# -------------------------------------------------------------------------- #
#                             Metric #4 Stamina                              #
# -------------------------------------------------------------------------- #
