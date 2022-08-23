from config.helper import *
from helpers.helper import *
from helpers.risk import *
from helpers.feedback import *
from helpers.score import *
from market.coinmarketcap import *
from validator.coinbase import *

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from support.database import get_db
from support.schemas import Coinbase_Item
from support import crud


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Scoring']
)


@router.post('/coinbase', status_code=status.HTTP_200_OK, summary='Coinbase credit score')
async def credit_score_coinbase(request: Request, item: Coinbase_Item, db: Session = Depends(get_db)):
    '''
    Calculates credit score based on Coinbase data.

    Input:
    - **coinbase_access_token [string]**: coinbase access token
    - **coinbase_refresh_token [string]**: coinbase refresh token
    - **coinmarketcap_key [string]**: coinmarketcap key
    - **loan_request [integer]**: loan request amount

    Output:
    - **[object]**: coinbase credit score
    '''

    try:
        print(f'\033[35;1m Receiving request from: {request.client.host}\033[0m')

        # configs
        print(f'\033[36m Accessing settings ...\033[0m')
        configs = read_config_file(item.loan_request)
        if isinstance(configs, str):
            raise Exception(configs)

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['coinbase']['thresholds']
        parm = configs['minimum_requirements']['coinbase']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])

        messages = configs['minimum_requirements']['coinbase']['messages']
        feedback = create_feedback(models)

        # coinmarketcap
        print(f'\033[36m Connecting with Coinmarketcap ...\033[0m')
        top_marketcap = coinmarketcap_currencies(
            item.coinmarketcap_key, thresholds['coinmarketcap_currencies'])
        if isinstance(top_marketcap, str):
            raise Exception(top_marketcap)

        # coinbase client connection
        print(f'\033[36m Connecting with validator ...\033[0m')
        client = coinbase_client(
            item.coinbase_access_token, item.coinbase_refresh_token)

        # coinbase supported currencies
        print(f'\033[36m Checking supported currencies 1/2 ...\033[0m')
        currencies = coinbase_currencies(client)
        if 'error' in currencies:
            raise Exception(currencies['error']['message'])

        # add top coinmarketcap currencies and coinbase currencies
        print(f'\033[36m Checking supported currencies 2/2 ...\033[0m')
        top_currencies = aggregate_currencies(
            top_marketcap, currencies, thresholds['odd_fiats'])

        # set native currency to USD
        print(f'\033[36m Setting native currency 1/2 ...\033[0m')
        native = coinbase_native_currency(client)
        if 'error' in native:
            raise Exception(native['error']['message'])
        if native != 'USD':
            set_native = coinbase_set_native_currency(client, 'USD')

        # data fetching
        print(f'\033[36m Reading data ...\033[0m')
        accounts, transactions = coinbase_accounts_and_transactions(
            client, top_currencies, thresholds['transaction_types'])
        if isinstance(accounts, str):
            raise Exception(f'Unable to fetch accounts data: {accounts}')
        if isinstance(transactions, str):
            raise Exception(f'Unable to fetch transactions data: {transactions}')

        # reset native currency
        print(f'\033[36m Setting native currency 2/2 ...\033[0m')
        set_native = coinbase_set_native_currency(client, native)

        # compute score and feedback
        print(f'\033[36m Calculating score ...\033[0m')
        score, feedback = coinbase_score(
            score_range, feedback, models, metrics, parm, accounts, transactions)

        # compute risk
        print(f'\033[36m Calculating risk ...\033[0m')
        risk = calc_risk(score, score_range, loan_range)

        # keep feedback data
        print(f'\033[36m Saving parameters ...\033[0m')
        data = keep_dict(score, feedback, risk, item.loan_request)
        crud.add_event(db, 'coinbase', data)

        # update feedback
        print(f'\033[36m Preparing feedback 1/2 ...\033[0m')
        message = qualitative_feedback_coinbase(
            messages, score, feedback, score_range, loan_range, qualitative_range, item.coinmarketcap_key)

        print(f'\033[36m Preparing feedback 2/2 ...\033[0m')
        feedback = interpret_score_coinbase(
            score, feedback, score_range, loan_range, qualitative_range)

        # return success
        print(f'\033[35;1m Credit score has successfully been calculated.\033[0m')
        return {
            'endpoint': '/credit_score/coinbase',
            'status': 'success',
            'score': int(score),
            'risk': risk,
            'message': message,
            'feedback': feedback
        }

    except Exception as e:
        print(f'\033[35;1m Unable to complete credit scoring calculation.\033[0m')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'endpoint': '/credit_score/coinbase',
                'status': 'error',
                'message': str(e),
            }
        )
