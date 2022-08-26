from config.helper import *
from helpers.helper import *
from helpers.risk import *
from helpers.feedback import *
from helpers.score import *
from market.coinmarketcap import *
from validator.plaid import *

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from support.database import get_db
from support.schemas import Plaid_Item
from support import crud

from dotenv import load_dotenv
from os import getenv
load_dotenv()


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Scoring']
)


@router.post('/plaid', status_code=status.HTTP_200_OK, summary='Plaid credit score')
async def credit_score_plaid(request: Request, item: Plaid_Item, db: Session = Depends(get_db)):
    '''
    Calculates credit score based on Plaid data.

    Input:
    - **plaid_access_token [string]**: plaid access token
    - **plaid_client_id [string]**: plaid client ID
    - **plaid_client_secret [string]**: plaid client secret
    - **coinmarketcap_key [string]**: coinmarketcap key
    - **loan_request [integer]**: loan request amount

    Output:
    - **[object]**: plaid credit score
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

        thresholds = configs['minimum_requirements']['plaid']['thresholds']
        period = thresholds['transactions_period']
        pagination = thresholds['transactions_pagination']
        parm = configs['minimum_requirements']['plaid']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['plaid']['scores']['models'])

        messages = configs['minimum_requirements']['plaid']['messages']
        feedback = create_feedback(models)
        feedback['fetch'] = {}

        # plaid client connection
        print(f'\033[36m Connecting with validator ...\033[0m')
        client = plaid_client(
            getenv('PLAID_ENV'), item.plaid_client_id, item.plaid_client_secret)

        # data fetching
        print(f'\033[36m Reading data ...\033[0m')
        dataset = plaid_transactions(item.plaid_access_token, client, pagination)
        if isinstance(dataset, dict) and 'error_code' in dataset:
            error = dataset['message']
            raise Exception(f'Unable to fetch transactions data: {error}')

        bank_name = plaid_bank_name(client, dataset['item']['institution_id'])
        feedback['diversity']['bank_name'] = bank_name

        # data formatting
        print(f'\033[36m Formatting data ...\033[0m')
        transactions = dataset['transactions']
        accounts = remove_key_dupes(dataset['accounts'], 'account_id')
        data = format_plaid_data(transactions, accounts)

        # validate loan request and transaction history
        print(f'\033[36m Validating template ...\033[0m')
        if not validate_loan_request(loan_range, accounts) or not validate_txn_history(period, data):
            value = loan_range[0]
            if value == 0:
                raise Exception(messages['not_qualified'])
            else:
                raise Exception(messages['not_qualified'].format(value))

        # compute score, feedback, and metadata
        print(f'\033[36m Calculating score ...\033[0m')
        score, feedback, metadata = plaid_score(data, score_range, feedback, models, metrics, parm, period)

        # compute risk
        print(f'\033[36m Calculating risk ...\033[0m')
        risk = calc_risk(score, score_range, loan_range)

        # keep metadata
        print(f'\033[36m Saving parameters ...\033[0m')
        data = keep_dict(score, metadata, risk, item.loan_request)
        crud.add_event(db, 'plaid', data)

        # update feedback
        print(f'\033[36m Preparing feedback 1/2...\033[0m')
        message = qualitative_feedback_plaid(
            messages, score, feedback, score_range, loan_range, qualitative_range, item.coinmarketcap_key)

        print(f'\033[36m Preparing feedback 2/2 ...\033[0m')
        feedback = interpret_score_plaid(
            score, feedback, score_range, loan_range, qualitative_range)

        # return success
        print(f'\033[35;1m Credit score has successfully been calculated.\033[0m')
        return {
            'endpoint': '/credit_score/plaid',
            'status': 'success',
            'score': int(score),
            'risk': risk,
            'message': message,
            'feedback': feedback
        }

    except Exception as e:
        print(f'\033[35;1m Unable to complete credit scoring calculation.\033[0m')
        error_msg = str(e)
        if 'do not qualify' in error_msg:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'endpoint': '/credit_score/plaid',
                    'status': 'not qualified',
                    'message': str(e),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'endpoint': '/credit_score/plaid',
                'status': 'error',
                'message': error_msg,
            }
        )
