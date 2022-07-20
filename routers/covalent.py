from testing.performance import *
from config.helper import *
from support.helper import *
from support.risk import *
from support.feedback import *
from support.score import *
from market.coinmarketcap import *
from validator.covalent import *
from schemas import *
from fastapi import APIRouter, Request, Response, HTTPException, status
from icecream import ic


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Score']
)


# @measure_time_and_memory
@router.post('/covalent', status_code=status.HTTP_200_OK, summary='Covalent credit score')
async def credit_score_covalent(request: Request, response: Response, item: Covalent_Item):
    '''
    Calculates credit score based on Covalent data.

    Input:
    - **eth_address [string]**: eth address
    - **covalent_key [string]**: covalentkey
    - **coinmarketcap_key [string]**: coinmarketcap key
    - **loan_request [integer]**: loan request amount

    Output:
    - **[object]**: covalent credit score
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

        thresholds = configs['minimum_requirements']['covalent']['thresholds']
        params = configs['minimum_requirements']['covalent']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])

        messages = configs['minimum_requirements']['covalent']['messages']
        feedback = create_feedback(models)
        feedback['fetch'] = {}

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(params)
        ic(models)
        ic(metrics)
        ic(messages)
        ic(feedback)

       # data fetching
        txn = covalent_get_transactions(
            '1', item.eth_address, item.covalent_key, False, 500, 0)
        balances = covalent_get_balances_or_portfolio(
            '1', item.eth_address, 'balances_v2', item.covalent_key)
        portfolio = covalent_get_balances_or_portfolio(
            '1', item.eth_address, 'portfolio_v2', item.covalent_key)

        # coinmarketcap
        erc_rank = coinmarektcap_top_erc(
            item.coinmarketcap_key,
            thresholds['coinmarketcap_currencies'],
            thresholds['erc_tokens']
        )
        ic(erc_rank)

        # compute score and feedback
        score, feedback = covalent_score(
            score_range,
            feedback,
            models,
            metrics,
            params,
            erc_rank,
            txn,
            balances,
            portfolio
        )
        ic(score)
        ic(feedback)

        # collect feedback
        collect = dict(feedback)
        collect['score'] = score
        collect['validator'] = 'covalent'
        collect['loan_request'] = item.loan_request
        file = path.join(root_dir(), 'support/feedback.json')
        append_json(collect, file)

        # compute risk
        risk = calc_risk(
            score,
            score_range,
            loan_range
        )
        ic(risk)

        # update feedback
        message = qualitative_feedback_covalent(
            messages,
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range,
            item.coinmarketcap_key
        )

        feedback = interpret_score_covalent(
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range
        )
        ic(message)
        ic(feedback)

        # return success
        status = 'success'

    except Exception as e:
        status = 'error'
        score = 0
        risk = 'undefined'
        message = str(e)
        feedback = {}

    finally:
        output = {
            'endpoint': '/credit_score/covalent',
            'status': status,
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
