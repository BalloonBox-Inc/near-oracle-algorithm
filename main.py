from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv
from os import getenv
from icecream import ic


# from validator.near import *
from validator.plaid import *
from validator.coinbase import *
from market.coinmarketcap import *
from support.score import *
from support.feedback import *
# from support.risk import *
from support.helper import *
from config.helper import *
from testing.performance import *


load_dotenv()


class Near_Item(BaseModel):
    coinmarketcap_key: str
    loan_request: int


class Plaid_Item(BaseModel):
    plaid_token: str
    plaid_client_id: str
    plaid_client_secret: str
    coinmarketcap_key: str
    loan_request: int


class Coinbase_Item(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str
    coinmarketcap_key: str
    loan_request: int


app = FastAPI()


def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


# @measure_time_and_memory
# @app.post('/credit_score/near')
# async def credit_score_near(item: Near_Item):
#     return output


# @measure_time_and_memory
@app.post('/credit_score/plaid')
async def credit_score_plaid(item: Plaid_Item):

    try:
        # client connection
        client = plaid_client(
            getenv('ENV'), item.plaid_client_id, item.plaid_client_secret)
        ic(client)

        # data fetching and formatting
        plaid_txn = plaid_transactions(item.plaid_token, client, 360)
        if 'error' in plaid_txn:
            raise Exception(plaid_txn['error']['message'])

        plaid_txn = {k: v for k, v in plaid_txn.items(
        ) if k in ['accounts', 'item', 'transactions']}
        plaid_txn['transactions'] = [
            t for t in plaid_txn['transactions'] if not t['pending']]

        # compute score
        feedback = create_feedback_plaid()
        feedback = plaid_bank_name(
            client, plaid_txn['item']['institution_id'], feedback)
        score, feedback = plaid_score(plaid_txn, feedback)
        message = qualitative_feedback_plaid(
            score, feedback, item.coinmarketcap_key)
        feedback = interpret_score_plaid(score, feedback)

        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        feedback = {}
        message = str(e)

    finally:
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/plaid',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'feedback': feedback,
            'message': message
        }
        if score == 0:
            output.pop('score', None)
            output.pop('feedback', None)
        ic(output)

        return output


# @measure_time_and_memory
@app.post('/credit_score/coinbase')
async def credit_score_coinbase(item: Coinbase_Item):

    try:
        # configs
        configs = read_config_file(item.loan_request)

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['coinbase']['thresholds']
        params = configs['minimum_requirements']['coinbase']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])

        feedback = create_feedback(models)
        messages = configs['minimum_requirements']['coinbase']['messages']

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(params)
        ic(models)
        ic(metrics)
        ic(feedback)
        ic(messages)

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
            raise Exception(accounts)

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)
        ic(set_native)

        # compute score and feedback
        score, feedback = coinbase_score(
            score_range,
            feedback,
            models,
            metrics,
            params,
            accounts,
            transactions
        )
        ic(score)
        ic(feedback)

        # compute risk
        # risk = calc_risk(
        #     score,
        #     score_range,
        #     loan_range
        # )

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
        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        feedback = {}
        message = str(e)

    finally:
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/coinbase',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            # 'risk': risk,
            'feedback': feedback,
            'message': message
        }
        if score == 0:
            output.pop('score', None)
            # output.pop('risk', None)
            output.pop('feedback', None)

        return output
