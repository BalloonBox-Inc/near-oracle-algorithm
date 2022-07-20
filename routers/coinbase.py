from testing.performance import *
from config.helper import *
from support.helper import *
from support.risk import *
from support.feedback import *
from support.score import *
from market.coinmarketcap import *
from validator.coinbase import *
from schemas import *
from fastapi import APIRouter, Request, Response, HTTPException, status
from icecream import ic


router = APIRouter(
    prefix='/credit_score',
    tags=['Credit Score']
)


# @measure_time_and_memory
@router.post('/coinbase', status_code=status.HTTP_200_OK, summary='Coinbase credit score')
async def credit_score_coinbase(request: Request, response: Response, item: Coinbase_Item):
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
        # configs
        configs = read_config_file(item.loan_request)
        if isinstance(configs, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Unable to read config file.')

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['coinbase']['thresholds']
        parm = configs['minimum_requirements']['coinbase']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])

        messages = configs['minimum_requirements']['coinbase']['messages']
        feedback = create_feedback(models)

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(parm)
        ic(models)
        ic(metrics)
        ic(messages)
        ic(feedback)

        # coinmarketcap
        top_marketcap = coinmarketcap_currencies(
            item.coinmarketcap_key,
            thresholds['coinmarketcap_currencies']
        )
        ic(top_marketcap)
        if isinstance(top_marketcap, str):
            raise Exception(top_marketcap)

        # coinbase client connection
        client = coinbase_client(
            item.coinbase_access_token,
            item.coinbase_refresh_token
        )
        ic(client)

        # coinbase supported currencies
        currencies = coinbase_currencies(client)
        ic(currencies)
        if 'error' in currencies:
            raise Exception(currencies['error']['message'])

        # add top coinmarketcap currencies and coinbase currencies
        top_currencies = aggregate_currencies(
            top_marketcap,
            currencies,
            thresholds['odd_fiats']
        )
        ic(top_currencies)

        # set native currency to USD
        native = coinbase_native_currency(client)
        if 'error' in native:
            raise Exception(native['error']['message'])
        if native != 'USD':
            set_native = coinbase_set_native_currency(client, 'USD')
        ic(native)

        # data fetching
        accounts, transactions = coinbase_accounts_and_transactions(
            client,
            top_currencies,
            thresholds['transaction_types']
        )
        ic(accounts)
        ic(transactions)
        if isinstance(accounts, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unable to fetch transactions data: {accounts}')

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)
        ic(set_native)

        # compute score and feedback
        score, feedback = coinbase_score(
            score_range,
            feedback,
            models,
            metrics,
            parm,
            accounts,
            transactions
        )
        ic(score)
        ic(feedback)

        # collect feedback
        collect = dict(feedback)
        collect['score'] = score
        collect['validator'] = 'coinbase'
        collect['loan_request'] = item.loan_request
        file = path.join(root_dir(), 'support/feedback.json')
        append_json(collect, file)

       # validate loan request
        if not validate_loan_request(
            loan_range, feedback, "liquidity", "avg_running_balance"
        ):
            raise Exception(messages["not_qualified"].format(loan_range[0]))

        # compute risk
        risk = calc_risk(
            score,
            score_range,
            loan_range
        )
        ic(risk)

        # update feedback
        message = qualitative_feedback_coinbase(
            messages,
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range,
            item.coinmarketcap_key
        )

        feedback = interpret_score_coinbase(
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
            'endpoint': '/credit_score/coinbase',
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
