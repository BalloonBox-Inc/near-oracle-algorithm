<p align="center">
  <a href="https://near.org/">
    <img alt="NearBlackLogo" src="https://github.com/BalloonBox-Inc/near-oracle-algorithm/blob/dev/images/logo_NearOracle_black.png" width="450" />
  </a>
</p>

# NearOracle API Docs

## About :mailbox_with_mail:

This documentation contains all APIs endpoints featured in our NearOracle dApp.

Imagine you are a user who owns a NEAR wallet and wants to be issued a loan.
The NearOracle dApp leverages public APIs to allow users to:

- integrate their existing Coinbase account, MetaMask wallet, or the financial institution with whom their bank with the NearOracle Credit Score model
- undergo a credit score check
- validate their credibility to lenders issuing them a loan

When using the NearOracle API you agree with our [Terms and Conditions](../LICENSE) :copyright:.

## To Notice :eyes:

#### Beware

All times provided are in UTC timezone :clock4:.

#### Authentication & Security

Every endpoint is secured by third parties authentication processes. The NearOracle dApp only have access to the data allowed by user. No user data is stored.

#### Help Us

Have you spotted a mistake in our API docs? Help us improve it by [letting us know](https://www.balloonbox.io/contact).

#### Caution

The API is in active development and we are changing things rapdily. Once we are ready to release a stable version of API we will notify the existing API owners.

## Resources :gear:

## [COINBASE](https://www.coinbase.com/) : credit score model based on Coinbase account

```bash
    POST {BASE_URL}/credit_score/coinbase
```

Headers

```bash
    {"Content-Type": "application/json"}
```

Body

```bash
    {
        "coinbase_access_token": "YOUR_COINBASE_ACCESS_TOKEN",
        "coinbase_refresh_token": "YOUR_COINBASE_REFRESH_TOKEN",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY",
        "loan_request": INTEGER_NUMBER
    }
```

Response: **200**

- Sample response from a Coinbase test account

```bash
    {
        "endpoint": "/credit_score/coinbase",
        "status": "success",
        "score": 300,
        "risk": {
            "loan_amount": 500,
            "risk_level": "high"
        },
        "message": "NearOracle could not calculate your credit score as there is no active wallet nor transaction history associated with your Coinbase account. Please use a different account.",
        "feedback": {
            "score": {
                "score_exist": false,
                "points": 300,
                "quality": "very poor",
                "loan_amount": null,
                "loan_duedate": null,
                "wallet_age(days)": null,
                "current_balance": null
            },
            "advice": {
                "kyc_error": false,
                "history_error": false,
                "liquidity_error": false,
                "activity_error": false,
            }
        }
    }
```

- Generalized Typescript response

```bash
    enum ScoreQuality {
        'very poor',
        'poor',
        'fair',
        'good',
        'very good',
        'excellent',
        'exceptional',
    }

    export interface IScoreResponseCoinbase {
        endpoint: '/credit_score/coinbase';
        status: 'success' | 'error';
        score: number;
        risk: {
            loan_amount: number;
            risk_level: 'low' | 'medium' | 'high';
        };
        message: string;
        feedback: {
            score: {
                score_exist: boolean;
                points: number;
                quality: ScoreQuality;
                loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
                loan_duedate: 3 | 4 | 5 | 6;
                wallet_age(days): number;
                current_balance: number;
            };
            advice: {
                kyc_error: boolean;
                history_error: boolean;
                liquidity_error: boolean;
                activity_error: boolean;
            };
        };
    }
```

Response: **400**

- Sample error response from a Coinbase test account requesting more than what is allowed for that template

```bash
    {
    "endpoint": "/credit_score/coinbase",
    "status": "error",
    "message": "Loan amount requested is over the limit."
    }
```

## [COVALENT](https://www.covalenthq.com/) : credit score model based on your ETH wallet address

```bash
    POST {BASE_URL}/credit_score/covalent
```

Headers

```bash
    {"Content-Type": "application/json"}
```

Body

```bash
      {
        "eth_address": "YOUR_ETH_WALLET_ADDRESS",
        "covalent_key": "FREE_COVALENT_API_KEY",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY",
        "loan_request": INTEGER_NUMBER
      }
```

Response: **200**

- Sample response for a test ETH address

```bash
    {
        "endpoint": "/credit_score/covalent",
        "status": "success",
        "score": 686,
        "risk": {
            "loan_amount": 10000,
            "risk_level": "medium"
        },
        "message": "Congrats, you have successfully obtained a credit score! Your NearOracle score is GOOD - 686 points. This score qualifies you for a short term loan of up to 2,340 NEAR which is equivalent to 10,000 USD over a recommended pay back period of 6 monthly installments. Your total balance across all cryptocurrencies is $1981.28 USD.",
        "feedback": {
            "score": {
                "score_exist": true,
                "points": 686,
                "quality": "good",
                "loan_amount": 10000,
                "loan_duedate": 6,
                "longevity(days)": null,
                "cum_balance_now": 1981.28
            },
            "advice": {
                "credibility_error": false,
                "wealth_error": false,
                "traffic_error": false,
                "stamina_error": false,
            }
        }
    }
```

- Generalized Typescript response

```bash
    enum ScoreQuality {
        'very poor',
        'poor',
        'fair',
        'good',
        'very good',
        'excellent',
        'exceptional',
    }

    export interface IScoreResponseCovalent {
        endpoint: '/credit_score/covalent';
        status: 'success' | 'error';
        score: number;
        risk: {
            loan_amount: number;
            risk_level: 'low' | 'medium' | 'high';
        };
        message: string;
        feedback: {
            score: {
                score_exist: boolean;
                points: number;
                quality: ScoreQuality;
                loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
                loan_duedate: 3 | 4 | 5 | 6;
                longevity(days): number;
                cum_balance_now: number;
            };
            advice: {
                credibility_error: boolean;
                wealth_error: boolean;
                traffic_error: boolean;
                stamina_error: boolean;
            };
        };
    }
```

Response: **400**

- Sample error response from a non-existing ETH wallet address

```bash
    {
        "endpoint": "/credit_score/covalent",
        "status": "error",
        "message": "Malformed address provided: 0xnonexistentethwalletaddressexample"
    }
```

## [PLAID](https://plaid.com/) : credit score model based on Plaid account

```bash
    POST {BASE_URL}/credit_score/plaid
```

Headers

```bash
    {"Content-Type": "application/json"}
```

Body

```bash
    {
        "plaid_access_token": "YOUR_PLAID_TOKEN",
        "plaid_client_id": "YOUR_PLAID_CLIENT_ID",
        "plaid_client_secret": "YOUR_CLIENT_SECRET",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY",
        "loan_request": INTEGER_NUMBER
    }
```

Response: **200**

- Sample response from Plaid Sandbox environment

```bash
    {
        "endpoint": "/credit_score/plaid",
        "status": "success",
        "score": 514,
        "risk": {
            "loan_amount": 1000,
            "risk_level": "high"
        },
        "message": "Congrats, you have successfully obtained a credit score! Your NearOracle score is POOR - 514 points. This score qualifies you for a short term loan of up to 234 NEAR which is equivalent to 1,000 USD over a recommended pay back period of 6 monthly installments. Your total current balance is $730 USD across all accounts held with Chase.",
        "feedback": {
            "score": {
                "score_exist": true,
                "points": 514,
                "quality": "poor",
                "loan_amount": 1000,
                "loan_duedate": 6,
                "card_names": null,
                "cum_balance": 730,
                "bank_accounts": 3
            },
            "advice": {
                "credit_exist": true,
                "credit_error": false,
                "velocity_error": false,
                "stability_error": false,
                "diversity_error": false,
            }
        }
    }
```

- Generalized Typescript response

```bash
    enum ScoreQuality {
        'very poor',
        'poor',
        'fair',
        'good',
        'very good',
        'excellent',
        'exceptional',
    }

    export interface IScoreResponsePlaid {
        endpoint: '/credit_score/plaid';
        status: 'success' | 'error' | 'not_qualified';
        score: number;
        risk: {
            loan_amount: number;
            risk_level: 'low' | 'medium' | 'high';
        };
        message: string;
        feedback: {
            score: {
                score_exist: boolean;
                points: number;
                quality: ScoreQuality;
                loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
                loan_duedate: 3 | 4 | 5 | 6;
                card_names: string;
                cum_balance: number;
                bank_accounts: number;
            };
            advice: {
                credit_exist: boolean;
                credit_error: boolean;
                velocity_error: boolean;
                stability_error: boolean;
                diversity_error: boolean;
            };
        };
    }
```

Response: **400**

- Sample error response from a wrong Plaid environment attempt

```bash
    {
        "endpoint": "/credit_score/coinbase",
        "status": "error",
        "message": "Unable to fetch transactions data: provided access token is for the wrong Plaid environment. expected \"sandbox\", got \"sand\""
    }
```

## KYC : KYC verification model

```bash
    POST {BASE_URL}/kyc
```

Headers

```bash
    {"Content-Type": "application/json"}
```

Body

```bash
      {
        "chosen_validator": "YOUR_CHOSEN_VALIDATOR",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY",

        "coinbase_access_token" [optional]: "YOUR_COINBASE_ACCESS_TOKEN",
        "coinbase_refresh_token" [optional]: "YOUR_COINBASE_REFRESH_TOKEN",

        "eth_address" [optional]: "YOUR_ETH_WALLET_ADDRESS",
        "covalent_key" [optional]: "FREE_COVALENT_API_KEY",

        "plaid_access_token" [optional]: "YOUR_PLAID_TOKEN",
        "plaid_client_id" [optional]: "YOUR_PLAID_CLIENT_ID",
        "plaid_client_secret" [optional]: "YOUR_CLIENT_SECRET"
      }
```

Response: **200**

- Sample response from Plaid Sandbox environment

```bash
    {
        "endpoint": "/kyc",
        "status": "success",
        "validator": "plaid",
        "kyc_verified": true,
    }
```

- Generalized Typescript response

```bash
    export interface IScoreResponseKYC {
        endpoint: '/kyc';
        status: 'success' | 'error';
        validator: 'coinbase' | 'covalent' | 'plaid';
        kyc_verified: boolean;
    }
```

Response: **400**

- Sample error response from an expired Coinbase access token

```bash
    {
        "endpoint": "/kyc",
        "status": "error",
        "message": "Unable to fetch accounts data: The access token expired"
    }
```
