from config.helper import *
from helpers.helper import *
from helpers.risk import *
from helpers.feedback import *
from helpers.score import *
from market.coinmarketcap import *
from validator.covalent import *

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from support.database import get_db
from support.schemas import Covalent_Item
from support import crud


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Scoring']
)


@router.post('/covalent', status_code=status.HTTP_200_OK, summary='Covalent credit score')
async def credit_score_covalent(request: Request, item: Covalent_Item, db: Session = Depends(get_db)):
    '''
    Calculates credit score based on Covalent data.

    Input:
    - **eth_address [string]**: eth address
    - **covalent_key [string]**: covalent key
    - **coinmarketcap_key [string]**: coinmarketcap key
    - **loan_request [integer]**: loan request amount

    Output:
    - **[object]**: covalent credit score
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

        thresholds = configs['minimum_requirements']['covalent']['thresholds']
        parm = configs['minimum_requirements']['covalent']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])

        messages = configs['minimum_requirements']['covalent']['messages']
        feedback = create_feedback(models)
        feedback['fetch'] = {}

       # data fetching
        print(f'\033[36m Reading data ...\033[0m')
        txn = covalent_get_transactions(
            '1', item.eth_address, item.covalent_key, False, 500, 0)
        if isinstance(txn, dict) and 'found_error' in txn and txn['found_error']:
            raise Exception(txn['error_message'])

        balances = covalent_get_balances_or_portfolio(
            '1', item.eth_address, 'balances_v2', item.
            covalent_key)
        if isinstance(balances, dict) and 'found_error' in balances and balances['found_error']:
            raise Exception(balances['error_message'])

        portfolio = covalent_get_balances_or_portfolio(
            '1', item.eth_address, 'portfolio_v2', item.covalent_key)
        if isinstance(portfolio, dict) and 'found_error' in portfolio and portfolio['found_error']:
            raise Exception(portfolio['error_message'])

        # coinmarketcap
        print(f'\033[36m Connecting with Coinmarketcap ...\033[0m')
        erc_rank = coinmarektcap_top_erc(
            item.coinmarketcap_key, thresholds['coinmarketcap_currencies'], thresholds['erc_tokens'])

        # compute score and feedback
        print(f'\033[36m Calculating score ...\033[0m')
        score, feedback = covalent_score(
            score_range, feedback, models, metrics, parm, erc_rank, txn, balances, portfolio)

        # compute risk
        print(f'\033[36m Calculating risk ...\033[0m')
        risk = calc_risk(score, score_range, loan_range)

        # keep feedback data
        print(f'\033[36m Saving parameters ...\033[0m')
        data = keep_dict(score, feedback, risk, item.loan_request)
        crud.add_event(db, 'covalent', data)

        # update feedback
        print(f'\033[36m Preparing feedback 1/2 ...\033[0m')
        message = qualitative_feedback_covalent(
            messages, score, feedback, score_range, loan_range, qualitative_range, item.coinmarketcap_key)

        print(f'\033[36m Preparing feedback 2/2 ...\033[0m')
        feedback = interpret_score_covalent(
            score, feedback, score_range, loan_range, qualitative_range)

        # return success
        print(f'\033[35;1m Credit score has successfully been calculated.\033[0m')
        return {
            'endpoint': '/credit_score/covalent',
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
                'endpoint': '/credit_score/covalent',
                'status': 'error',
                'message': str(e),
            }
        )
