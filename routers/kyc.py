from config.helper import *
from helpers.helper import *
from market.coinmarketcap import *
from validator.plaid import *
from validator.coinbase import *
from validator.covalent import *
from helpers.metrics_plaid import *
from helpers.metrics_coinbase import *
from helpers.metrics_covalent import *

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from support.schemas import KYC_Item

from dotenv import load_dotenv
from os import getenv
load_dotenv()


router = APIRouter(
    tags=['KYC Verification']
)


@router.post('/kyc', status_code=status.HTTP_200_OK, summary='Verify KYC')
async def credit_score_kyc(request: Request, item: KYC_Item):
    '''
    Verifies chosen account (Coinbase, Covalent, or Plaid) through set of rules to determine whether KYC or not.

    Input:
    - **chosen_validator [string]**: chosen validator
    - **plaid_access_token [string | Optional]**: plaid access token
    - **plaid_client_id [string | Optional]**: plaid client ID
    - **plaid_client_secret [string | Optional]**: plaid client secret
    - **coinbase_access_token [string | Optional]**: coinbase access token
    - **coinbase_refresh_token [string | Optional]**: coinbase refresh token
    - **coinmarketcap_key [string | Optional]**: coinmarketcap key
    - **eth_address [string | Optional]**: eth address
    - **covalent_key [string | Optional]**: covalentkey

    Output:
    - **[object]**: kyc verification
    '''

    try:
        print(f'\033[35;1m Receiving request from: {request.client.host}\033[0m')

        # configs
        print(f'\033[36m Accessing settings ...\033[0m')
        configs = read_config_file(0)
        if isinstance(configs, str):
            raise Exception(configs)

        thresholds = configs['minimum_requirements'][item.chosen_validator]['thresholds']

        # kyc models
        if item.chosen_validator == 'coinbase':
            # coinmarketcap
            print(f'\033[36m Connecting with Coinmarketcap ...\033[0m')
            top_marketcap = coinmarketcap_currencies(
                item.coinmarketcap_key, thresholds['coinmarketcap_currencies'])

            if isinstance(top_marketcap, str):
                raise Exception(f'Unable to fetch coinmarketcap data: {top_marketcap}')

            # coinbase client connection
            print(f'\033[36m Connecting with validator ...\033[0m')
            client = coinbase_client(
                item.coinbase_access_token, item.coinbase_refresh_token)

            # coinbase supported currencies
            print(f'\033[36m Checking supported currencies 1/2 ...\033[0m')
            currencies = coinbase_currencies(client)

            if 'error' in currencies:
                error = currencies['error']['message']
                raise Exception(f'Unable to fetch coinbase data: {error}')

            # add top coinmarketcap currencies and coinbase currencies
            print(f'\033[36m Checking supported currencies 2/2 ...\033[0m')
            top_currencies = aggregate_currencies(
                top_marketcap, currencies, thresholds['odd_fiats'])

            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            accounts, transactions = coinbase_accounts_and_transactions(
                client, top_currencies, thresholds['transaction_types'])

            if isinstance(accounts, str):
                raise Exception(f'Unable to fetch accounts data: {accounts}')

            if isinstance(transactions, str):
                raise Exception(f'Unable to fetch transactions data: {transactions}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = coinbase_kyc(accounts, transactions)

        elif item.chosen_validator == 'covalent':
            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            transactions = covalent_get_transactions(
                '1', item.eth_address, item.covalent_key, False, 500, 0)

            if isinstance(transactions, dict) and 'found_error' in transactions and transactions['found_error']:
                error = transactions['error_message']
                raise Exception(f'Unable to fetch transactions data: {error}')

            balances = covalent_get_balances_or_portfolio(
                '1', item.eth_address, 'balances_v2', item.covalent_key)

            if isinstance(balances, dict) and 'found_error' in balances and balances['found_error']:
                error = balances['error_message']
                raise Exception(f'Unable to fetch balances data: {error}')

            portfolio = covalent_get_balances_or_portfolio(
                '1', item.eth_address, 'portfolio_v2', item.covalent_key)

            if isinstance(portfolio, dict) and 'found_error' in portfolio and portfolio['found_error']:
                error = portfolio['error_message']
                raise Exception(f'Unable to fetch portfolio data: {error}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = covalent_kyc(transactions, balances, portfolio)

        elif item.chosen_validator == 'plaid':
            # plaid client connection
            print(f'\033[36m Connecting with validator ...\033[0m')
            client = plaid_client(
                getenv('PLAID_ENV'), item.plaid_client_id, item.plaid_client_secret)

            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            dataset = plaid_transactions(item.plaid_access_token, client, thresholds['transactions_period'])

            if isinstance(dataset, dict) and 'error_code' in dataset:
                error = dataset['message']
                raise Exception(f'Unable to fetch transactions data: {error}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = plaid_kyc(dataset['accounts'], dataset['transactions'])

        # return success
        print(f'\033[35;1m Account has successfully been KYC verified.\033[0m')
        return {
            'endpoint': '/kyc',
            'status': 'success',
            'validator': item.chosen_validator,
            'kyc_verified': kyc_verified
        }

    except Exception as e:
        print(f'\033[35;1m Unable to complete KYC verification.\033[0m')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'endpoint': '/kyc',
                'status': 'error',
                'message': str(e),
            }
        )
