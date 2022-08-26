from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.country_code import CountryCode
from plaid.api import plaid_api
from helpers.helper import flatten_list
from datetime import timedelta
from datetime import datetime
from icecream import ic
import plaid
import json


def plaid_environment(plaid_env):
    if plaid_env == 'sandbox':
        host = plaid.Environment.Sandbox

    if plaid_env == 'development':
        host = plaid.Environment.Development

    if plaid_env == 'production':
        host = plaid.Environment.Production

    return host


def plaid_client(plaid_env, client_id, secret):
    config = plaid.Configuration(
        host=plaid_environment(plaid_env),
        api_key={
            'clientId': client_id,
            'secret': secret
        }
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def format_error(e):
    r = json.loads(e.body)
    error = {
        'status_code': e.status,
        'message': r['error_message'],
        'error_code': r['error_code'],
        'error_type': r['error_type']
    }
    ic(error)
    return error


def plaid_transactions(access_token, client, pagination_limit):

    start_date = (datetime.now() - timedelta(days=1800))  # max of 5 years of data
    end_date = datetime.now()
    txn = list()
    plaid_max_fetch = 500  # https://plaid.com/docs/api/products/transactions/#transactionsget

    try:
        options = TransactionsGetRequestOptions()
        options.count = plaid_max_fetch

        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date(),
            options=options
        )

        r = client.transactions_get(request).to_dict()
        if 'error' in r:
            raise Exception(r['error']['message'])

        txn_count = len(r['transactions'])
        txn_total_count = r['total_transactions']

        # calling other pages if exists
        if txn_total_count != txn_count:
            extra_pages = int(txn_total_count / txn_count)
            extra_pages = min(extra_pages, pagination_limit)

            for n in range(extra_pages):
                options = TransactionsGetRequestOptions()
                options.offset = txn_count
                options.count = plaid_max_fetch

                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                    options=options
                )
                rn = client.transactions_get(request).to_dict()
                if 'error' in rn:
                    raise Exception(rn['error']['message'])

                txn.append(rn['transactions'])
                txn_count += len(rn['transactions'])

        # first page data only
        data = {k: v for k, v in r.items()
                if k in ['accounts', 'item', 'transactions']}

        # add other pages data if exists
        if txn:
            txn = flatten_list(txn)  # other pages
            lst = data['transactions']  # first page
            lst.extend(txn)
            data['transactions'] = lst

        # remove pending transactions
        data['transactions'] = [t for t in data['transactions'] if not t['pending']]

    except plaid.ApiException as e:
        data = format_error(e)

    finally:
        return data


def plaid_bank_name(client, bank_id):
    '''
        Description:
        returns the bank name where the user holds his bank account

    Parameters:
        client (plaid.api.plaid_api.PlaidApi): plaid client info (api key, secret key, palid environment)
        bank_id (str): the Plaid ID of the institution to get details about

    Returns:
        bank_name (str): name of the bank uwhere user holds their fundings
    '''
    try:
        request = InstitutionsGetByIdRequest(
            institution_id=bank_id,
            country_codes=list(map(lambda x: CountryCode(x), ['US']))
        )

        r = client.institutions_get_by_id(request)
        r = r['institution']['name']

    except:
        r = None

    finally:
        return r
