from testing.performance import *
from config.helper import *
from support.helper import *
from support.risk import *
from support.feedback import *
from support.score import *
from market.coinmarketcap import *
from validator.plaid import *
from validator.coinbase import *
from validator.covalent import *
from schemas import *
from fastapi import APIRouter, Request, Response, HTTPException, status
from icecream import ic


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
    - **plaid_access_token [string | Optional]**: plaid access token
    - **plaid_client_id [string | Optional]**: plaid client ID
    - **plaid_client_secret [string | Optional]**: plaid client secret
    - **coinbase_access_token [string | Optional]**: coinbase access token
    - **coinbase_refresh_token [string | Optional]**: coinbase refresh token
    - **eth_address [string | Optional]**: eth address
    - **covalent_key [string | Optional]**: covalentkey
    - **coinmarketcap_key [string]**: coinmarketcap key
    - **loan_request [integer]**: loan request amount

    Output:
    - **[object]**: kyc credit score
    '''

    return {'status': 'under construction'}
