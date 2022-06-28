import numpy as np
from datetime import datetime

NOW = datetime.now().date()

# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #
def swiffer_duster(txn, feedback):
    '''
    Description:
        remove 'dust' transactions (i.e., transactions with less than $0.1 in spot fiat value get classified as dust) and
        keep only 'successful' transactions (i.e., transactions that got completed).

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback

    Returns:
        txn (dict): formatted txn data containing only successful and non-dusty transactions
    '''
    try: 
        if txn['quote_currency'] == 'USD':
            success_only = []
            for t in txn['items']:
                # keep only transactions that are successful and have a value > 0
                if t['successful'] and t['value_quote'] > 0:
                    success_only.append(t)

            txn['items'] = success_only
            if txn['items']:
                return txn
            else:
                raise Exception("txn data should be a dict, but is NoneType")
        else:
            raise Exception("quote_currency should be USD, but it isn't")

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


def top_erc_only(data, feedback, top_erc):
    ''' 
    Description:
        filter the Covalent API data by keeping only the assets in the ETH 
        wallet address which are top ranked on Coinmarketcap as ERC20 tokens
    
    Parameters:
        data (dict): can be either the 'balances_v2' or the 'portfolio_v2' Covalent class A endpoint
        feedback (dict): score feedback
        top_erc (list): list of ERC tokens ranked highest on Coinmarketcap

    Returns:
        data (dict): containing only top ERC tokens. All other tokens will NOT
        count toward the credit score and are disregarded altogether
    '''
    try:
        for b in data['items']:
            if 'contract_ticker_symbol' not in b.keys():
                raise KeyError('you passed invalid data. This function \
                    only accepts the endpoints: balances_v2 and portfolio_v2')
            else:
                if b['contract_ticker_symbol'] not in top_erc:
                    data['items'].remove(b)
        return data

    except Exception as e:
        feedback['fetch']['error'] = str(e)

# -------------------------------------------------------------------------- #
#                            Metric #1 Credibility                           #
# -------------------------------------------------------------------------- #
def credibility_kyc(balances, txn, feedback):
    '''
    Description:
        checks whether an ETH wallet address has legitimate transaction history and active balances

    Parameters:
        balances (dict): Covalent class A endpoint 'balances_v2'
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback

    Returns:
        score (float): 1 if KYC'ed and 0
        feedback (dict): updated score feedback
    '''
    try:
        # Assign max score as long as the user owns some credible 
        # non-zero balance accounts with some transaction history
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
        how_long = (NOW - oldest).days

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
        across ALL tokens owned (regardless fo their Coinmarketcap ranking)

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


def wealth_capital_now_adjusted(balances, feedback, erc_rank, fico_medians, volume_now):
    ''' 
    Description:
        adjusted tot balance of token owned (USD). Accounts for the Coinmarketcap ranking of the token owned

    Parameters:
        balances (dict): Covalent class A endpoint 'balances_v2'
        feedback (dict): score feedback
        fico_medians (array): score bins
        volume_now (array): bins for the total token volume owned now

    Returns:
        score (float): points for cumulative balance now (adjusted)
        feedback (dict): updated score feedback
    '''
    try:
        # Keep only balances data of top rankes ERC tokens
        top_erc = list(erc_rank.keys())
        balances = top_erc_only(balances, feedback, top_erc)

        adjusted_balance = 0
        for b in balances['items']:
            balance = b['quote']
            ticker = b['contract_ticker_symbol']
            # multiply the balance owned per token by a weight proportional to that token's ranking on Coinmarketcap
            penalty = np.e**(erc_rank[ticker]**(1/3.5) )
            adjusted_balance += round(1 - penalty / 100, 2) * balance

            score = fico_medians[np.digitize(adjusted_balance, volume_now, right=True)]
            feedback['wealth']['cum_balance_now(adjusted)'] = round(adjusted_balance, 2)

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
        # remove 'dust' transactions from youw dataset
        txn = swiffer_duster(txn, feedback)
        
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
def traffic_cred_deb(txn, feedback, operation, count_operations, cred_deb, mtx_traffic):
    '''
    Description:
        rewarding points proportionally to the count and volume of credit and debit transactions

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        operation (str): accepts 'credit', 'debit', or 'transfer'
        count_operations (array): bins transaction count
        cred_deb (array): bins transaction volume
        mtx_traffic (array): score matrix 

    Returns:
        score (float): for the count and volume of credit or debit transactions
        feedback (dict): updated score feedback
    '''
    try:
        # remove 'dust' transactions from youw dataset
        txn = swiffer_duster(txn, feedback)

        counts = 0
        volume = 0
        eth_wallet = txn['address']

        # credit
        if operation == 'credit':
            for t in txn['items']:
                if t['to_address'] == eth_wallet:
                    counts += 1
                    volume += t['value_quote']   
            count_operations = count_operations/2 
            cred_deb = cred_deb/2    

        # debit
        elif operation == 'debit':
            for t in txn['items']:
                if t['from_address'] == eth_wallet:
                    counts += 1
                    volume += t['value_quote']

        # transfer
        elif operation == 'transfer':
            for t in txn['items']:
                if eth_wallet not in [t['from_address'], t['to_address']]:
                    indx = txn['items'].index(t)
                    if txn['items'][indx]['log_events'][0]['decoded']['name'] == 'Transfer':
                        counts += 1
                        volume += t['value_quote']
            count_operations = count_operations/5
            cred_deb = cred_deb/2 

        # except
        else:
            raise Exception("you apssed an invalid param: accepts only 'credit', 'debit', or 'transfer'")


        m = np.digitize(counts, count_operations, right=True)
        n = np.digitize(volume, cred_deb, right=True)
        score = mtx_traffic[m][n]
        feedback['traffic']['count_credit_txns'] =  counts
        feedback['traffic']['volume_credit_txns'] = round(volume, 2)

    except Exception as e:
        score = 0
        feedback['traffic']['error'] = str(e)

    finally:
        return score, feedback


def traffic_dustiness(txn, feedback, fico_medians):
    '''
    Description:
        accounts for legitimate transactions over total transactions
        (assuming some transactions are dust, i.e., < $0.1 value)

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        fico_medians (array): scoring array

    Returns:
        score (float): the more dusty txn the lower the score
        feedback (dict): updated score feedback
    '''
    try:
        legit_ratio = (len(txn['items']) - len(swiffer_duster(txn, feedback)['items'])) / len(txn['items'])
        score = fico_medians[np.digitize(legit_ratio, fico_medians*0.8, right=True)]
        feedback['traffic']['legit_txn_ratio'] = round(legit_ratio, 2)

    except Exception as e:
        score = 0
        feedback['traffic']['error'] = str(e)

    finally:
        return score, feedback


def traffic_running_balance(portfolio, feedback, fico_medians, avg_run_bal, top_erc):
    '''
    Description:
        score earned based on the average running balance 
        of your best token over the past 30 days

    Parameters:
        portfolio (dict): Covalent class A endpoint 'portfolio_v2'
        feedback (dict): score feedback
        fico_medians (array): scoring array
        avg_run_bal (array): bins for avg running balance
        top_erc (list): list of ERC tokens ranked highest on Coinmarketcap

    Returns:
        score (float): points earned for the average running 
            balance (over the last month) of the best token owned
        feedback (dict): updated score feedback
    '''
    try:
        # keep only top ERC on Coinmarketcap
        portfolio = top_erc_only(portfolio, feedback, top_erc)
        overview = {}

        for p in portfolio['items']:
            sum = 0
            count = 0
            ticker = p['contract_ticker_symbol']
            for q in p['holdings']:
                sum += q['close']['quote']
                count += 1
            avg = sum/count
            overview[ticker] = avg

        best_avg = max(overview.values())
        score = fico_medians[np.digitize(best_avg, avg_run_bal, right=True)]
        feedback['traffic']['avg_running_balance(best_token)'] = round(best_avg, 2)

    except Exception as e:
        score = 0
        feedback['traffic']['error'] = str(e)

    finally:
        return score, feedback


def traffic_frequency(txn, feedback, fico_medians, frequency_txn):
    '''
    Description:
        reward wallet address with frequent monthly transactions

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        fico_medians (array): scoring array
        frequency_txn (array): bins for transaction frequency

    Returns:
        score (float): the more frequent transactions the higher the score
        feedback (dict): updated score feedback
    '''
    try:
        # remove 'dust' transactions from youw dataset
        txn = swiffer_duster(txn, feedback)
        
        datum = txn['items'][-1]['block_signed_at'].split('T')[0]
        oldest = datetime.strptime(datum, '%Y-%M-%d').date()
        duration = int((NOW - oldest).days/30) # months

        frequency = round(len(txn['items']) / duration , 2)
        score = fico_medians[np.digitize(frequency, frequency_txn, right=True)]
        feedback['traffic']['txn_frequency'] = f'{frequency} txn/month over {duration} months'

    except Exception as e:
        score = 0
        feedback['traffic']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                             Metric #4 Stamina                              #
# -------------------------------------------------------------------------- #
def stamina_methods_count(txn, feedback, fico_medians, count_to_four):
    '''
    Description:
        rewards the user for the number of distinct methods they performed in their 
        transaction history and for the volume of currency traded for each unique method

    Parameters:
        txn (dict): Covalent class A endpoint 'transactions_v2'
        feedback (dict): score feedback
        fico_medians (array): binning rewarding percentages of the score
        count_to_four (array): binning the count of unique methods

    Returns:
        score (float): points for the number of unique methods and their volume
        feedback (dict): updated score feedback
    '''
    try:
        # remove 'dust' transactions from youw dataset
        txn = swiffer_duster(txn, feedback)
        methods = {}

        for t in txn['items']:
            amount = t['value_quote']
            if t['log_events']:
                method_name = t['log_events'][0]['decoded']['name']
                if method_name in methods.keys():
                    methods[method_name] += amount
                else: 
                    methods[method_name] = amount
            else:
                if 'unclassified' in methods.keys():
                    methods['unclassified'] += amount
                else:
                    methods['unclassified'] = amount

        methods_count = len([k for k in methods.keys() if methods[k] > 50])
        score = fico_medians[np.digitize(methods_count, count_to_four, right=True)]
        feedback['stamina']['unique_methods_count'] = methods_count

    except Exception as e:
        score = 0
        feedback['stamina']['error'] = str(e)
    
    finally:
        return score, feedback


def stamina_coins_count(balances, feedback, count_to_four, volume_now, mtx_stamina, erc_rank):
    '''
    Description:
        How many cryptocurrencies does the wallet address own? 
        What is the tot weighted volume owned right now?

    Parameters:
        balances (dict): Covalent class A endpoint 'balances_v2'
        feedback (dict): score feedback
        count_to_four (array): bins counting the distinct coins owned
        volume_now (array): bins for the total token volume owned now
        mtx_stamina (array): 2D scoring grid
        erc_rank (dict): list of top Coinmarektcap ERC20 tokens and their ranks

    Returns:
        score (float): rewards points for the number of coins owned and their tot weighted balance
        feedback (dict): updated score feedback
    '''
    try:
        # keep only top ERC on Coinmarketcap
        balances = top_erc_only(balances, feedback, list(erc_rank.keys()))

        weighted_sum = 0
        volumes = [b['quote'] for b in balances['items'] if b['quote'] != 0]
        ranks = [erc_rank[b['contract_ticker_symbol']] for b in balances['items'] if b['quote'] != 0]
        unique_coins = len(volumes)

        for b in balances['items']:
            if b['quote'] != 0:
                weight = (min(ranks) / (b['quote']/min(ranks)) ) / sum(ranks)
                weighted_sum += b['quote']*weight

        m = np.digitize(unique_coins, count_to_four, right=True)
        n = np.digitize(weighted_sum, volume_now*0.5, right=True)
        score = mtx_stamina[m][n]
        feedback['stamina']['coins_count'] = unique_coins

    except Exception as e:
        score = 0
        feedback['stamina']['error'] = str(e)

    finally:
        return score, feedback


def stamina_dexterity(portfolio, feedback, count_to_four, volume_now, mtx_stamina):
    '''
    Description:
        does this user buy when the market is low and sell when the market is high? 
        Let's call the operation of buying in bear market and selling in bullish a smart trade
        How often do smart trades occur? 
        How much caputail is traded cumulatives across ALL smart trades?

    Parameters:
        portfolio (dict): Covalent class A endpoint 'portfolio_v2'
        feedback (dict): score feedback
        count_to_four (array): bins counting the distinct coins owned
        volume_now (array): bins for the total token volume owned now
        mtx_stamina (array): 2D scoring grid

    Returns:
        score (float): rewarding the count and the tot voume of smart trades
        feedback (dict): updated score feedback
    '''
    try:
        portfolio = purge_portfolio(portfolio, feedback)

        for p in portfolio['items']:
            quote_rates = np.array([q['quote_rate'] for q in p['holdings']])
            trades = np.array([q['high']['quote'] - q['low']['quote'] for q in p['holdings']])
            x = int(len(p['holdings'])/3)

            # does this user buy when the market is bearish?
            bear_indeces = np.argpartition(quote_rates, x)[:x]
            bear_trades = [t for t in trades[bear_indeces] if t > 0]

            # does this user sell when the market is bullish?
            bull_indeces = np.argpartition(quote_rates, x*2)[-x:]
            bull_trades = [t for t in trades[bull_indeces] if t >0]
            
        count = len(bear_trades) + len(bull_trades)
        traded = sum(bear_trades) + sum(bull_trades)

        m = np.digitize(count, count_to_four, right=True)
        n = np.digitize(traded, volume_now/10, right=True)
        score = mtx_stamina[m][n]
        feedback['stamina']['count_smart_trades'] = count

    except Exception as e:
        score = 0
        feedback['stamina']['error'] = str(e)

    finally:
        return score, feedback