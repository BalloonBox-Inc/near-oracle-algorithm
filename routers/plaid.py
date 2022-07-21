from testing.performance import *
from config.helper import *
from support.helper import *
from support.risk import *
from support.feedback import *
from support.score import *
from market.coinmarketcap import *
from validator.plaid import *
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
@router.post('/plaid', status_code=status.HTTP_200_OK, summary='Plaid credit score')
async def credit_score_plaid(request: Request, response: Response, item: Plaid_Item):
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
        # configs
        configs = read_config_file(item.loan_request)
        if isinstance(configs, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Unable to read config file.')

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['plaid']['thresholds']
        parm = configs['minimum_requirements']['plaid']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['plaid']['scores']['models'])

        penalties = read_model_penalties(
            configs['minimum_requirements']['plaid']['scores']['models'])

        messages = configs['minimum_requirements']['plaid']['messages']
        feedback = create_feedback(models)
        feedback['fetch'] = {}

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(parm)
        ic(models)
        ic(metrics)
        ic(penalties)
        ic(messages)
        ic(feedback)

        # plaid client connection
        client = plaid_client(
            getenv('ENV'),
            item.plaid_client_id,
            item.plaid_client_secret
        )
        ic(client)

        # data fetching
        transactions = plaid_transactions(
            item.plaid_access_token,
            client,
            thresholds['transactions_period']
        )
        if isinstance(transactions, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unable to fetch transactions data: {transactions}')

        bank_name = plaid_bank_name(
            client,
            transactions['item']['institution_id'],
        )
        feedback['diversity']['bank_name'] = bank_name
        ic(bank_name)

        # compute score and feedback
        score, feedback = plaid_score(
            transactions,
            score_range,
            feedback,
            models,
            penalties,
            metrics,
            parm
        )
        ic(score)
        ic(feedback)

        # validate loan request and transaction history
        if not validate_loan_request(
            loan_range, feedback, "stability", "cumulative_current_balance"
        ) or not validate_txn_history(
            thresholds["transactions_period"], feedback, "stability", "txn_history"
        ):
            raise Exception(messages["not_qualified"].format(loan_range[0]))

        # keep feedback data
        data = keep_feedback(feedback, score, item.loan_request, 'plaid')

        # compute risk
        risk = calc_risk(
            score,
            score_range,
            loan_range
        )
        ic(risk)

        # update feedback
        message = qualitative_feedback_plaid(
            messages,
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range,
            item.coinmarketcap_key
        )

        feedback = interpret_score_plaid(
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range
        )
        ic(message)
        ic(feedback)

        # return success
        status_msg = 'success'

    except Exception as e:
        status_msg = 'error'
        score = 0
        risk = 'undefined'
        message = str(e)
        feedback = {}

    finally:
        output = {
            'endpoint': '/credit_score/plaid',
            'status': status_msg,
            'score': int(score),
            'risk': risk,
            'message': message,
            'feedback': feedback
        }
        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        return output
