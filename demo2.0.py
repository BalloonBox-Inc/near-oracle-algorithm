import json
from os import getenv
from dotenv import load_dotenv
from validator.covalent import *
from icecream import ic

from testing.performance import *
from config.helper import *
from support.helper import *
from support.risk import *
from support.feedback import *
from support.score import *
from market.coinmarketcap import *
from validator.covalent import *


load_dotenv()


def write_to_json(count, eth_address, blockchain_id, covalent_key, path):
    '''
    Write Covalent data to disk as json files
    '''
    # fetch data through Covalent API
    txn = covalent_get_transactions(
        blockchain_id, eth_address, covalent_key, False, 500, 0)

    balances = covalent_get_balances_or_portfolio(
        blockchain_id, eth_address, 'balances_v2', covalent_key)

    portfolio = covalent_get_balances_or_portfolio(
        blockchain_id, eth_address, 'portfolio_v2', covalent_key)

    dict = {'balances':balances, 'portfolio':portfolio, 'txn':txn}

    for name, dict_ in dict.items():
        with open(f'{path}{count}_{name}.json', 'w') as f:
            json.dump(dict_, f, indent=3)



def read_json(userid, path):
    '''
    Read Covalent json files from local storage
    '''
    with open(f'{path}{str(userid)}_balances.json', 'r') as f:
        balances = json.load(f)

    with open(f'{path}{str(userid)}_txn.json', 'r') as f:
        txn = json.load(f)

    with open(f'{path}{str(userid)}_portfolio.json', 'r') as f:
        portfolio = json.load(f)

    return balances, txn, portfolio



def compute_covalent_score(balances, txn, portfolio, coinmarketcap_key, loan_request):
    try:
        # configs
        configs = read_config_file(loan_request)

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

       # no need to fetch data, since data was already 
       # passed as arguments to this function

        # coinmarketcap
        erc_rank = coinmarektcap_top_erc(
            coinmarketcap_key,
            thresholds['coinmarketcap_currencies'],
            thresholds['erc_tokens']
        )

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
            coinmarketcap_key
        )

        interpret = interpret_score_covalent(
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range
        )
        ic(message)
        ic(interpret)

        # return success
        status = 'success'

    except Exception as e:
        status = 'error'
        score = 0
        risk = 'undefined'
        message = str(e)
        feedback = {}
        interpret = 'error'

    finally:
        output = {
            'status': status,
            'score': int(score),
            'risk': risk,
            'message': message,
            'feedback': feedback,
            'interpret': interpret
        }
        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

    return output



if __name__ == '__main__':

    # # write to json
    # addresses = getenv('WALLETS')
    # for x in addresses:
    #     write_to_json(addresses.index(x), x, '1', getenv('COVALENT_KEY'), getenv('COV_DIR'))

    # iteratively compute scores
    for y in range(11):
        balances, txn, portfolio = read_json(y, getenv('COV_DIR'))
        print(balances['address'])
        r = compute_covalent_score(balances, txn, portfolio, getenv('COINMARKETCAP_KEY'), 24000)