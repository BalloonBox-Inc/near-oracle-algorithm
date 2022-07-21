from testing.performance import *
from config.helper import *
from support.helper import *
from market.coinmarketcap import *
from validator.plaid import *
from validator.coinbase import *
from validator.covalent import *
from support.metrics_plaid import *
from support.metrics_coinbase import *
from support.metrics_covalent import *
from schemas import *
from fastapi import APIRouter, Request, Response, HTTPException, status
from icecream import ic
from dotenv import load_dotenv
from os import getenv
load_dotenv()


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Score']
)


# @measure_time_and_memory
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
        # configs
        configs = read_config_file(0)
        if isinstance(configs, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Unable to read config file.')

        thresholds = configs['minimum_requirements'][item.chosen_validator]['thresholds']
        ic(thresholds)

        # kyc models
        ic(item.chosen_validator)
        if item.chosen_validator == 'plaid':
            # plaid client connection
            client = plaid_client(
                getenv('ENV'), item.plaid_client_id, item.plaid_client_secret)
            ic(client)

            # data fetching
            transactions = plaid_transactions(
                item.plaid_access_token, client, thresholds['transactions_period'])
            if isinstance(transactions, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch transactions data: {transactions}')

            # verify kyc
            kyc_verified = plaid_kyc(transactions)

        elif item.chosen_validator == 'coinbase':
            # coinmarketcap
            top_marketcap = coinmarketcap_currencies(
                item.coinmarketcap_key, thresholds['coinmarketcap_currencies'])
            if isinstance(top_marketcap, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch coinmarketcap data: {top_marketcap}')

            # coinbase client connection
            client = coinbase_client(
                item.coinbase_access_token, item.coinbase_refresh_token)
            ic(client)

            # coinbase supported currencies
            currencies = coinbase_currencies(client)
            if 'error' in currencies:
                error = currencies['error']['message']
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unable to fetch coinbase data: {error}')

            # add top coinmarketcap currencies and coinbase currencies
            top_currencies = aggregate_currencies(
                top_marketcap, currencies, thresholds['odd_fiats'])

            # data fetching
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
            kyc_verified = coinbase_kyc(accounts, transactions)

        elif item.chosen_validator == 'covalent':
            # data fetching
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
            kyc_verified = covalent_kyc(balances, transactions)

        # return success
        status_msg = 'success'
        ic(kyc_verified)

    except Exception as e:
        status_msg = 'error'
        kyc_verified = False

    finally:
        return {
            'endpoint': '/credit_score/kyc',
            'status': status_msg,
            'validator': item.chosen_validator,
            'kyc_verified': kyc_verified
        }
