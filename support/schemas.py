from pydantic import BaseModel
from typing import Optional


# http request classes
class CoinmarketCap_Access(BaseModel):
    coinmarketcap_key: str


class Coinbase_Access(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str


class Covalent_Access(BaseModel):
    eth_address: str
    covalent_key: str


class Plaid_Access(BaseModel):
    plaid_access_token: str
    plaid_client_id: str
    plaid_client_secret: str


class Loan_Item(BaseModel):
    loan_request: int


class Coinbase_Item(
        Coinbase_Access, CoinmarketCap_Access, Loan_Item):
    pass


class Covalent_Item(
        Covalent_Access, CoinmarketCap_Access, Loan_Item):
    pass


class Plaid_Item(
        Plaid_Access, CoinmarketCap_Access, Loan_Item):
    pass


class KYC_Item(BaseModel):
    chosen_validator: str
    coinmarketcap_key: str

    plaid_access_token: Optional[str]
    plaid_client_id: Optional[str]
    plaid_client_secret: Optional[str]

    coinbase_access_token: Optional[str]
    coinbase_refresh_token: Optional[str]

    eth_address: Optional[str]
    covalent_key: Optional[str]
