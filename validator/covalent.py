import requests
from icecream import ic

def format_err(e):
    '''
    format the error output when fetching Covalent data. 
    Covalent API returns JSON responses with the same shape for all endpoints
    '''
    error = {
        'found_error': e['error'],
        'error_message': e['error_message'],
        'error_code': e['error_code']
    }
    ic(error)
    return error


def covalent_get_balances_or_portfolio(chain_id, eth_address, endpoints, api_key):
    '''
    get historical portfolio value over time or token balances for an address. 
    This function works for 2 endpoints: either 'balances_v2' or 'portfolio_v2' 
    '''
    try:
        endpoint = f'/{chain_id}/address/{eth_address}/{endpoints}/?key={api_key}'
        url = 'https://api.covalenthq.com/v1' + endpoint
        result = requests.get(url).json()
        if result['error']:
            r = format_err(result)
        else:
            r = result['data']

    except requests.exceptions.JSONDecodeError:
        r = 'JSONDecodeError: invalid Covalent API key'

    finally:
        return r


def covalent_get_transactions(chain_id, eth_address, api_key, no_logs, pagesize, pagenumber):
    '''
    Description:
        get all transactions for a given address. This endpoint does a deep-crawl 
        of the blockchain to retrieve all kinds of transactions/transfers that 
        references the address including indexed topics within the event logs

    Parameters:
        chain_id (int): blockchain id 
        eth_address (str): wallet address to fetch txn data from
        api_key (str): Covalent api key to for the https request
        no_logs (bool): choose whether to include log events in the return object
        pagesize (int): number of results per page
        pagenumber (int): the specific page to be returned

    Returns: 
        r (dict): the txn history for a wallet address
    '''
    try:
        endpoint = f'/{chain_id}/address/{eth_address}/transactions_v2/'\
                f'?no-logs={no_logs}&page-size={pagesize}&page-number={pagenumber}&key={api_key}'
        url = 'https://api.covalenthq.com/v1' + endpoint
        result = requests.get(url).json()

        if result['error']:
            r = format_err(result)

        else:
            txn = result['data']
            
            while pagenumber < 3:
                if txn['pagination']['has_more']:
                    pagenumber += 1
                    endpoint = f'/{chain_id}/address/{eth_address}/transactions_v2/'\
                            f'?no-logs={no_logs}&page-size={pagesize}&page-number={pagenumber}&key={api_key}'
                    url = 'https://api.covalenthq.com/v1' + endpoint
                    result = requests.get(url).json()
                    txn_next = result['data']
                    txn['items'] = txn['items'] + txn_next['items']
            r = txn
    
    except requests.exceptions.JSONDecodeError:
        r = 'JSONDecodeError: invalid Covalent API key'

    finally:
        return r


def covalent_get_transfers(chain_id, eth_address, api_key, pagesize, pagenumber):
    '''
    Description:
        get ERC20 token transfers for an address

    Parameters:
        chain_id (int): blockchain id 
        eth_address (str): wallet address to fetch txn data from
        api_key (str): Covalent api key to for the https request
        pagesize (int): number of results per page
        pagenumber (int): the specific page to be returned

    Returns: 
        r (dict): the transfer history for a wallet address
    '''
    try:
        endpoint = f'/{chain_id}/address/{eth_address}/transfers_v2/'\
                f'?page-size={pagesize}&page-number={pagenumber}&key={api_key}'
        url = 'https://api.covalenthq.com/v1' + endpoint
        result = requests.get(url).json()
        if result['error']:
            r = format_err(result)
        else:
            r = result['data']
    
    except requests.exceptions.JSONDecodeError:
        r = 'JSONDecodeError: invalid Covalent API key'

    finally:
        return r