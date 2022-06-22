import numpy as np
from datetime import datetime

# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #
def swiffer_duster(txn, feedback):
    '''
    Description:
        remove 'dust' transactions (i.e., transactions with less than $0.1 in spot fiat value get classified as dust) and
        keep only 'successful' transactions (i.e., transactions that got completed). Whenever you call the 'swiffer_duster' 
        function, ensure it returns an output different than a NoneType

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback

    Returns:
        txn (dict): formatted txn data containing only successful and non-dusty transactions
    '''
    try: 
        success_only = []
        for t in txn['items']:
            # keep only transactions that are successful and have a value > 0
            if t['successful'] and t['value_quote'] > 0:
                success_only.append(t)

        txn['items'] = success_only
        return txn

    except Exception as e:
        feedback['fetch'][swiffer_duster.__name__] = str(e)


def purge_portfolio(portfolio, feedback):
    '''
    Description:
        remove 'dusty' tokens from portfolio. That is, we xonsider only those tokens 
        that had a closing day balance of >$50 for at least 3 days in the last month

    Parameters:
        portfolio (dict): Covalent class A endpoint 'portfolio_v2'
        feedback (dict): score feedback

    Returns:
        portfolio (dict): purged portfolio without dusty tokens
    '''
    try: 
        # ensure the quote currency is USD. If it isn't, then raise an exception
        if portfolio['quote_currency'] != 'USD':
            raise Exception('quote_currency should be USD')
        else:
            print(len(portfolio['items']))
            counts = list()
            for a in portfolio['items']:
                count = 0
                for b in a['holdings']:
                    if b['close']['quote'] > 50:
                        count += 1
                    # exist the loop as soon as the count exceeds 3
                    if count > 2:
                        break
                counts.append(count)

            # remove dusty token from the records
            for i in range(len(counts)):
                if counts[i] < 3:
                    portfolio['items'].pop(i)

            print(len(portfolio['items']))
        return portfolio
            
    except Exception as e:
        feedback['fetch'][purge_portfolio.__name__] =  str(e)

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
