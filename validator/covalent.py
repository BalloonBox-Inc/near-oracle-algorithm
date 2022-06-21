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


def covalent_balances_or_portfolio(chain_id, eth_address, endpoints, api_key):
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


def covalent_txn_or_transfers(chain_id, eth_address, api_key, endpoints, no_logs, pagesize, pagenumber):
    '''
    get all transactions for a given address OR  get ERC20 token transfers for an address. 
    This endpoint does a deep-crawl of the blockchain to retrieve all kinds of transactions/transfers 
    that references the address including indexed topics within the event logs

            Parameters:
                chain_id (int): blockchain id 
                eth_address (str): wallet address to fetch txn data from
                api_key (str): Covalent api key to for the https request
                endpoints (str): Covalent endpoint. It can be either 'transactions_v2' or 'transfers_v2'
                no_logs (bool): choose whether to include log events in the return object
                pagesize (int): number of results per page
                pagenumber (int): the specific page to be returned

            Returns: 
                r (dict): the txn history for a wallet address
    '''
    try:
        if endpoints == 'transactions_v2':
            endpoint = f'/{chain_id}/address/{eth_address}/{endpoints}/'\
                f'?no-logs={no_logs}&page-size={pagesize}&page-number={pagenumber}&key={api_key}'
        elif endpoints == 'transfers_v2':
            endpoint = f'/{chain_id}/address/{eth_address}/{endpoints}/'\
                f'?page-size={pagesize}&page-number={pagenumber}&key={api_key}'
        else: 
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