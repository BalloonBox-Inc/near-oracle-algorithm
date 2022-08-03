from pydantic import BaseModel
from typing import Optional


class Plaid_Item(BaseModel):
    plaid_access_token: str
    plaid_client_id: str
    plaid_client_secret: str
    coinmarketcap_key: str
    loan_request: int
    user: int


class Coinbase_Item(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str
    coinmarketcap_key: str
    loan_request: int


class Covalent_Item(BaseModel):
    eth_address: str
    covalent_key: str
    coinmarketcap_key: str
    loan_request: int


class KYC_Item(BaseModel):
    chosen_validator: str
    plaid_access_token: Optional[str]
    plaid_client_id: Optional[str]
    plaid_client_secret: Optional[str]
    coinbase_access_token: Optional[str]
    coinbase_refresh_token: Optional[str]
    coinmarketcap_key: Optional[str]
    eth_address: Optional[str]
    covalent_key: Optional[str]
