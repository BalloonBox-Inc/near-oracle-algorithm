from market.coinmarketcap import *
import numpy as np


# Some helper functions
def comma_separated_list(l):
    '''Takes a Pyhton list as input and returns a string of comma separated elements with AND at the end'''
    if len(l) == 1:
        msg = l[0]
    elif len(l) == 2:
        msg = l[0]+' and '+l[1]
    else:
        msg = ', '.join(l[:-1]) + ', and ' + l[-1]

    return msg


# -------------------------------------------------------------------------- #
#                                   Plaid                                    #
# -------------------------------------------------------------------------- #
def create_interpret_plaid():
    '''
   Description:
        Initializes a dict with a concise summary to communicate and interpret the NEARoracle score. 
        It includes the most important metrics used by the credit scoring algorithm (for Plaid).
    '''
    return {
        'score': {
            'score_exist': False,
            'points': None,
            'quality': None,
            'loan_amount': None,
            'loan_duedate': None,
            'card_names': None,
            'cum_balance': None,
            'bank_accounts': None
        },
        'advice': {
            'credit_exist': False,
            'credit_error': False,
            'velocity_error': False,
            'stability_error': False,
            'diversity_error': False
        }
    }


def interpret_score_plaid(score, feedback, score_range, loan_range, quality_range):
    '''
    Description:
        returns a dict explaining the meaning of the numerical score

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on main Plaid metrics

    Returns:
        interpret (dict): dictionaries with the major contributing score metrics 
    '''
    try:
        # Create 'interpret' dict to interpret the numerical score
        interpret = create_interpret_plaid()

        # Score
        if feedback['fetch']:
            interpret['score']['points'] = 300
            interpret['score']['quality'] = 'very poor'
        else:
            interpret['score']['score_exist'] = True
            interpret['score']['points'] = int(score)
            interpret['score']['quality'] = quality_range[np.digitize(
                score, score_range, right=False)]
            interpret['score']['loan_amount'] = int(
                loan_range[np.digitize(score, score_range, right=False)])

            if ('loan_duedate' in list(feedback['stability'].keys())):
                interpret['score']['loan_duedate'] = int(
                    feedback['stability']['loan_duedate'])

            if ('card_names' in list(feedback['credit'].keys())) and (feedback['credit']['card_names']):
                interpret['score']['card_names'] = [c.capitalize()
                                                    for c in feedback['credit']['card_names']]

            if 'cumulative_current_balance' in list(feedback['stability'].keys()):
                interpret['score']['cum_balance'] = feedback['stability']['cumulative_current_balance']

            if 'bank_accounts' in list(feedback['diversity'].keys()):
                interpret['score']['bank_accounts'] = feedback['diversity']['bank_accounts']

        # Advice
            if 'no credit card' not in list(feedback['credit'].values()):
                interpret['advice']['credit_exist'] = True

            if 'error' in list(feedback['credit'].keys()):
                interpret['advice']['credit_error'] = True

            if 'error' in list(feedback['velocity'].keys()):
                interpret['advice']['velocity_error'] = True

            if 'error' in list(feedback['stability'].keys()):
                interpret['advice']['stability_error'] = True

            if 'error' in list(feedback['diversity'].keys()):
                interpret['advice']['diversity_error'] = True

    except Exception as e:
        interpret = str(e)

    finally:
        return interpret


def qualitative_feedback_plaid(
    messages, score, feedback, score_range, loan_range, quality_range, coinmarketcap_key):
    '''
    Description:
        A function to format and return a qualitative description 
        of the numerical score obtained by the user

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on main Plaid metrics

    Returns:
        msg (str): qualitative message explaining the numerical score to the user. 
        Return this message to the user in the front end of the Dapp
    '''

    # SCORE
    all_keys = [x for y in [list(feedback[k].keys())
                for k in feedback.keys()] for x in y]

    # Case #1: NO score exists. 
    # --> return fetch error when the Oracle did not 
    # --> fetch any data and computed no score
    if feedback['fetch']:
        msg = messages['failed']
        return msg

    # Case #2: a score exists.
    # --> return descriptive score feedback
    # Declare score variables
    quality = quality_range[np.digitize(score, score_range, right=False)]
    points = int(score)
    loan_amount = int(loan_range[np.digitize(score, score_range, right=False)])

    # Communicate the score
    rate = coinmarketcap_rate(coinmarketcap_key, 'USD', 'NEAR')
    msg = messages['success'].format(
            quality.upper(), points, int(round(loan_amount*rate, 0)), loan_amount)

    if ('loan_duedate' in list(feedback['stability'].keys())):
        payback = feedback['stability']['loan_duedate']
        msg = msg + f' over a recommended pay back period of {payback} monthly installments.'

    # Interpret the score
    # Credit cards
    if ('card_names' in all_keys) and (feedback['credit']['card_names']):
        msg = msg + ' Part of your score is based on the transaction history of your {} credit card'.format(
            ', '.join([c for c in feedback['credit']['card_names']]))
        if len(feedback['credit']['card_names']) > 1:
            msg = msg + 's'

    # Tot balance now
    if 'cumulative_current_balance' in all_keys:
        bal = feedback['stability']['cumulative_current_balance']
        bank = feedback['diversity']['bank_name']
        msg = msg + f' Your total current balance is ${bal:,.0f} USD across all accounts held with {bank}.'

    # ADVICE
    # Case #1: there's error(s). 
    # Either some functions broke or data is missing.
    if 'error' in all_keys:

        # Subcase #1.1: the error is that no credit card exists
        if 'no credit card' in list(feedback['credit'].values()):
            msg = msg + f' NEARoracle found no credit card associated with your bank account. '\
                        f'Credit scores rely heavily on credit card history. Improve your score '\
                        f'by selecting a different bank account which shows credit history'

        # Subcase #1.2: the error is elsewhere
        else:
            metrics_w_errors = [k for k in feedback.keys(
            ) if 'error' in list(feedback[k].keys())]
            err = comma_separated_list(metrics_w_errors)
            msg = msg + f' An error occurred while computing the score metric called {err}. '\
                        f'As a result, your score was rounded down. Try again later or select '\
                        f'an alternative bank account if you have one'
    return msg + '.'


# -------------------------------------------------------------------------- #
#                                  Coinbase                                  #
# -------------------------------------------------------------------------- #
def create_interpret_coinbase():
    '''
   Description:
        Initializes a dict with a concise summary to communicate and interpret the NEARoracle score. 
        It includes the most important metrics used by the credit scoring algorithm (for Coinbase).
    '''
    return {
        'score': {
            'score_exist': False,
            'points': None,
            'quality': None,
            'loan_amount': None,
            'loan_duedate': None,
            'wallet_age(days)': None,
            'current_balance': None
        },
        'advice': {
            'kyc_error': False,
            'history_error': False,
            'liquidity_error': False,
            'activity_error': False
        }
    }


def interpret_score_coinbase(score, feedback, score_range, loan_range, quality_range):
    '''
    Description:
        returns a dict explaining the meaning of the numerical score

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on main Coinbase metrics

    Returns:
        interpret (dict): dictionaries with the major contributing score metrics 
    '''
    try:
        # Create 'interpret' dict to interpret the numerical score
        interpret = create_interpret_coinbase()

        # Score
        if ('kyc' in feedback.keys()) & (feedback['kyc']['verified'] == False):
            interpret['score']['points'] = 300
            interpret['score']['quality'] = 'very poor'
        else:
            interpret['score']['score_exist'] = True
            interpret['score']['points'] = int(score)
            interpret['score']['quality'] = quality_range[np.digitize(
                score, score_range, right=False)]
            interpret['score']['loan_amount'] = int(
                loan_range[np.digitize(score, score_range, right=False)])
            interpret['score']['loan_duedate'] = int(
                feedback['liquidity']['loan_duedate'])

            if ('wallet_age(days)' in list(feedback['history'].keys())) and \
                (feedback['history']['wallet_age(days)']):
                interpret['score']['wallet_age(days)'] = feedback['history']['wallet_age(days)']

            if 'current_balance' in list(feedback['liquidity'].keys()):
                interpret['score']['current_balance'] = feedback['liquidity']['current_balance']

        # Advice
            if 'error' in list(feedback['kyc'].keys()):
                interpret['advice']['kyc_error'] = True

            if 'error' in list(feedback['history'].keys()):
                interpret['advice']['history_error'] = True

            if 'error' in list(feedback['liquidity'].keys()):
                interpret['advice']['liquidity_error'] = True

            if 'error' in list(feedback['activity'].keys()):
                interpret['advice']['activity_error'] = True

    except Exception as e:
        interpret = str(e)

    finally:
        return interpret


def qualitative_feedback_coinbase(
    messages, score, feedback, score_range, loan_range, quality_range, coinmarketcap_key):
    '''
    Description:
        A function to format and return a qualitative description
        of the numerical score obtained by the user

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on main Coinbase metrics

    Returns:
        msg (str): qualitative message explaining the numerical score to the user. 
        Return this message to the user in the front end of the Dapp
    '''

    # SCORE
    all_keys = [x for y in [list(feedback[k].keys())
                for k in feedback.keys()] for x in y]

    # Case #1: NO score exists. 
    # --> return fetch error when the Oracle did not 
    # --> fetch any data and computed no score
    if 'kyc' in feedback.keys() and \
        feedback['kyc']['verified'] == False:
        msg = messages['failed']
        return msg

    # Case #2: a score exists. 
    # --> return descriptive score feedback
    # Declare score variables
    quality = quality_range[np.digitize(score, score_range, right=False)]
    points = int(score)
    loan_amount = int(loan_range[np.digitize(score, score_range, right=False)])

    # Communicate the score
    rate = coinmarketcap_rate(coinmarketcap_key, 'USD', 'NEAR')
    msg = messages['success'].format(
        quality.upper(), points, int(round(loan_amount*rate, 0)), loan_amount)

    if ('loan_duedate' in list(feedback['liquidity'].keys())):
        payback = feedback['liquidity']['loan_duedate']
        msg = msg + f' over a recommended pay back period of {payback} monthly installments.'

    # Coinbase account duration
    if ('wallet_age(days)' in all_keys):
        if ('current_balance' in all_keys):
            lon = feedback['history']['wallet_age(days)']
            bal = feedback['liquidity']['current_balance']
            msg = msg + f' Your Coinbase account has been active for {lon} days '\
                f'and your total balance across all wallets is ${bal:,.0f} USD'
        else:
            lon = feedback['history']['wallet_age(days)']
            msg = msg + f' Your Coinbase account has been active for {lon} days'

    # Tot balance
    else:
        if ('current_balance' in all_keys):
            bal = feedback['liquidity']['current_balance']
            msg = msg + f' Your total balance across all wallets is ${bal} USD'

    # ADVICE
    # Case #1: there's error(s).
    # Either some functions broke or data is missing.
    if 'error' in all_keys:
        metrics_w_errors = [k for k in feedback.keys(
        ) if 'error' in list(feedback[k].keys())]
        err = comma_separated_list(metrics_w_errors)
        msg = msg + f' An error occurred while computing the score metric called {err}. '\
            f'As a result, your score was rounded down. Try to log into Coinbase again later'
    return msg + '.'


# -------------------------------------------------------------------------- #
#                                  Covalent                                  #
# -------------------------------------------------------------------------- #
def create_interpret_covalent():
    '''
   Description:
        Initializes a dict with a concise summary to communicate and interpret the NEARoracle score. 
        It includes the most important metrics used by the credit scoring algorithm (for Covalent).
    '''
    return {
        'score': {
            'score_exist': False,
            'points': None,
            'quality': None,
            'loan_amount': None,
            'loan_duedate': None,
            'longevity(days)': None,
            'cum_balance_now': None
        },
        'advice': {
            'credibility_error': False,
            'wealth_error': False,
            'traffic_error': False,
            'stamina_error': False
        }
    }


def interpret_score_covalent(score, feedback, score_range, loan_range, quality_range):
    '''
    Description:
        returns a dict explaining the meaning of the numerical score

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on major Covalent metrics

    Returns:
        interpret (dict): dictionaries with the major contributing score metrics 
    '''
    try:
        # Create 'interpret' dict to interpret the numerical score
        interpret = create_interpret_covalent()

        # Score
        if 'credibility' in feedback.keys() and \
            feedback['credibility']['verified'] == False:
            interpret['score']['points'] = 300
            interpret['score']['quality'] = 'very poor'
            
        else:
            interpret['score']['score_exist'] = True
            interpret['score']['points'] = int(score)
            interpret['score']['quality'] = quality_range[np.digitize(
                score, score_range, right=False)]
            interpret['score']['loan_amount'] = int(
                loan_range[np.digitize(score, score_range, right=False)])
            interpret['score']['loan_duedate'] = int(
                feedback['stamina']['loan_duedate'])

            if ('longevity(days)' in list(feedback['credibility'].keys())) and \
                (feedback['credibility']['longevity(days)']):
                interpret['score']['longevity(days)'] = feedback['credibility']['longevity(days)']

            if 'cum_balance_now' in list(feedback['wealth'].keys()):
                interpret['score']['cum_balance_now'] = feedback['wealth']['cum_balance_now']

        # Advice
            if 'error' in list(feedback['credibility'].keys()):
                interpret['advice']['credibility_error'] = True

            if 'error' in list(feedback['wealth'].keys()):
                interpret['advice']['wealth_error'] = True

            if 'error' in list(feedback['traffic'].keys()):
                interpret['advice']['traffic_error'] = True

            if 'error' in list(feedback['stamina'].keys()):
                interpret['advice']['stamina_error'] = True

    except Exception as e:
        interpret = str(e)

    finally:
        return interpret


def qualitative_feedback_covalent(
    messages, score, feedback, score_range, loan_range, quality_range, coinmarketcap_key):
    '''
    Description:
        A function to format and return a qualitative description 
        of the numerical score obtained by the user

    Parameters:
        score (float): user's NEARoracle numerical score
        feedback (dict): score feedback, reporting stats on main Covalent metrics

    Returns:
        msg (str): qualitative message explaining the numerical score to the user. 
        Return this message to the user in the front end of the Dapp
    '''

    # SCORE
    all_keys = [x for y in [list(feedback[k].keys()) 
                for k in feedback.keys()] for x in y]

    # Case #1: NO score exists. 
    # --> return fetch error when the Oracle did not 
    # --> fetch any data and computed no score
    if 'credibility' in feedback.keys() and \
        feedback['credibility']['verified'] == False:
        msg = messages['failed']
        return msg

    # Case #2: a score exists. 
    # --> return descriptive score feedback
    # Declare score variables
    quality = quality_range[np.digitize(score, score_range, right=False)]
    points = int(score)
    loan_amount = int(loan_range[np.digitize(score, score_range, right=False)])

    # Communicate the score
    rate = coinmarketcap_rate(coinmarketcap_key, 'USD', 'NEAR')
    msg = messages['success'].format(
        quality.upper(), points, int(round(loan_amount*rate, 0)), loan_amount)

    if ('loan_duedate' in list(feedback['stamina'].keys())):
        payback = feedback['stamina']['loan_duedate']
        msg = msg + f' over a recommended pay back period of {payback} monthly installments.'

    # Covalent account duration
    if ('longevity(days)' in all_keys):
        if ('cum_balance_now' in all_keys):
            lon = feedback['credibility']['longevity(days)']
            bal = feedback['wealth']['cum_balance_now']
            msg = msg + f' Your ETH wallet address has been active for {lon} days '\
                f'and your total balance across all cryptocurrencies owned is ${bal:,.0f} USD'
        else:
            bal = feedback['wealth']['cum_balance_now']
            msg = msg + f' Your ETH wallet address has been active for {bal} days'
    # Tot balance
    else:
        if ('cum_balance_now' in all_keys):
            bal = feedback['wealth']['current_balance']
            msg = msg + f' Your total balance across all cryptocurrencies owned is ${bal} USD'

    # ADVICE
    # Case #1: there's error(s). 
    # Either some functions broke or data is missing.
    if 'error' in all_keys:
        metrics_w_errors = [k for k in feedback.keys(
        ) if 'error' in list(feedback[k].keys())]
        err = comma_separated_list(metrics_w_errors)
        msg = msg + f' An error occurred while computing the score metric called {err}. ' \
            f'As a result, your score was rounded down. Try to log into MetaMask again later'
    return msg + '.'       