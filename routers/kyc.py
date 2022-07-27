from support.assessment import *
from config.helper import *
from support.helper import *
from market.coinmarketcap import *
from validator.plaid import *
from validator.coinbase import *
from validator.covalent import *
from support.metrics_plaid import *
from support.metrics_coinbase import *
from support.metrics_covalent import *
from routers.schemas import *
from fastapi import APIRouter, Request, Response, HTTPException, status
from dotenv import load_dotenv
from os import getenv
load_dotenv()


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Score']
)


# @evaluate_function
@router.post('/kyc', status_code=status.HTTP_200_OK, summary='KYC credit score')
async def credit_score_kyc(request: Request, response: Response, item: KYC_Item):
    '''
    Calculates credit score based on KYC data from one of the validators.

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Unable to read config file.')

        thresholds = configs['minimum_requirements'][item.chosen_validator]['thresholds']

        # kyc models
        if item.chosen_validator == 'plaid':
            # plaid client connection
            print(f'\033[36m Connecting with validator ...\033[0m')
            client = plaid_client(
                getenv('ENV'), item.plaid_client_id, item.plaid_client_secret)

            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            transactions = plaid_transactions(
                item.plaid_access_token, client, thresholds['transactions_period'])
            if isinstance(transactions, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch transactions data: {transactions}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = plaid_kyc(transactions)

        elif item.chosen_validator == 'coinbase':
            # coinmarketcap
            print(f'\033[36m Connecting with Coinmarketcap ...\033[0m')
            top_marketcap = coinmarketcap_currencies(
                item.coinmarketcap_key, thresholds['coinmarketcap_currencies'])
            if isinstance(top_marketcap, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch coinmarketcap data: {top_marketcap}')

            # coinbase client connection
            print(f'\033[36m Connecting with validator ...\033[0m')
            client = coinbase_client(
                item.coinbase_access_token, item.coinbase_refresh_token)

            # coinbase supported currencies
            print(f'\033[36m Checking supported currencies 1/2 ...\033[0m')
            currencies = coinbase_currencies(client)
            if 'error' in currencies:
                error = currencies['error']['message']
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch coinbase data: {error}')

            # add top coinmarketcap currencies and coinbase currencies
            print(f'\033[36m Checking supported currencies 2/2 ...\033[0m')
            top_currencies = aggregate_currencies(
                top_marketcap, currencies, thresholds['odd_fiats'])

            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            accounts, transactions = coinbase_accounts_and_transactions(
                client, top_currencies, thresholds['transaction_types'])
            if isinstance(accounts, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch accounts data: {accounts}')
            if isinstance(transactions, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch transactions data: {transactions}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = coinbase_kyc(accounts, transactions)

        elif item.chosen_validator == 'covalent':
            # data fetching
            print(f'\033[36m Reading data ...\033[0m')
            balances = covalent_get_balances_or_portfolio(
                '1', item.eth_address, 'balances_v2', item.covalent_key)
            if isinstance(balances, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch balances data: {balances}')
            transactions = covalent_get_transactions(
                '1', item.eth_address, item.covalent_key, False, 500, 0)
            if isinstance(transactions, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch transactions data: {transactions}')

            # verify kyc
            print(f'\033[36m Verifying KYC ...\033[0m')
            kyc_verified = covalent_kyc(balances, transactions)

        # return success
        print(f'\033[35;1m Account has successfully been KYC verified.\033[0m')
        status_msg = 'success'

    except Exception as e:
        print(f'\033[35;1m Unable to complete KYC verification.\033[0m')
        status_msg = 'error'
        kyc_verified = False

    finally:
        return {
            'endpoint': '/credit_score/kyc',
            'status': status_msg,
            'validator': item.chosen_validator,
            'kyc_verified': kyc_verified
        }
