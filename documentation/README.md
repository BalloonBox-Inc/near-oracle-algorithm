<p align="center">
  <a href="https://near.org/">
    <img alt="NearWhiteLogo" src="https://github.com/BalloonBox-Inc/NEARoracle-Oracle/blob/dev/images/inverted-primary-logo-bg.png" width="450" />
  </a>
</p>

# NEAR ORACLE API

## About :mailbox_with_mail:

This documentation contains all APIs endpoints featured in our NEARoracle DApp.

Imagine you are a user who owns a NEAR wallet and wants to be issued a loan.
The NEARoracle DApp leverages public APIs to allow users to:

- integrate their existing Plaid, Coinbase, and NEAR wallet accounts with the NEARoracle Credit Score model,
- undergo a credit score check,
- validate their credibility to lenders issuing them a loan.

When using the NEARoracle API you agree with our [Terms and Conditions](https://) :copyright:.

## To Notice :eyes:

#### Beware

All times provided are in UTC timezone :clock4:.

#### Authentication

Every endpoint is secured by either a User Oauth token or by the pair Oauth Client key & secret key.

#### Help Us

Have you spotted a mistake in our API docs? Help us improve it by [letting us know](https://www.balloonbox.io/contact).

#### Caution

The API is in active development and we are changing things rapdily. Once we are ready to release a stable version of API we will notify the existing API owners.

## Resources :gear:

## [COINBASE](https://coinmarketcap.com/) : credit score model based on Coinbase account.

```bash
    POST {base_url}/credit_score/coinbase
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
    feedback: {
        advice: {
            activity_error: boolean;
            history_error: boolean;
            kyc_error: boolean;
            liquidity_error: boolean;
        };
        score: {
            current_balance: number;
            loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
            loan_duedate: 3 | 4 | 5 | 6;
            points: number;  # integer in range [300, 900]
            quality: ScoreQuality;
            score_exist: boolean;
            wallet_age(days): number;
        };
    };
    message: string;
    score: number;
    risk: {
        loan_amount: number;
        risk_level: 'low' | 'medium' | 'high';
    };
    status: 'success' | 'error';
    status_code: 200 | 400;
    timestamp: string;
    title: 'Credit Score';
    }
```

- Sample response from a Coinbase test account

```bash
{
    "endpoint": "/credit_score/coinbase",
    "feedback": {
        "advice": {
            "activity_error": false,
            "history_error": false,
            "kyc_error": false,
            "liquidity_error": false
        },
        "score": {
            "current_balance": null,
            "loan_amount": null,
            "loan_duedate": null,
            "points": null,
            "quality": null,
            "score_exist": false,
            "wallet_age(days)": null
        }
    },
    "message": "NEARoracle could not calculate your credit score because there is no active wallet nor transaction history <br/>
    in your Coinbase account. Try to log into Coinbase with a different account.",
    "risk": {
        "loan_amount": 500,
        "risk_level": "medium"
    }
    "score": 300.0,
    "status": "success",
    "status_code": 200,
    "timestamp": "03-22-2022 18:44:19 GMT",
    "title": "Credit Score"
}
```

## [PLAID](https://plaid.com/) : credit score model based on Plaid account.

```bash
    POST {base_url}/credit_score/plaid
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
    feedback: {
        advice: {
            credit_error: boolean;
            credit_exist: boolean;
            diversity_error: boolean;
            stability_error: boolean;
            velocity_error: boolean;
        };
        score: {
            bank_accounts: number;
            card_names: string[];
            cum_balance: number;
            loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
            loan_duedate: 3 | 4 | 5 | 6;
            points: number; # integer in range [300, 900]
            quality: ScoreQuality;
            score_exist: boolean;
        };
    };
    message: string;
    score: number;
    risk: {
            loan_amount: number;
            risk_level: 'low' | 'medium' | 'high';
    };
    status: 'success' | 'error';
    status_code: 200 | 400;
    timestamp: string;
    title: 'Credit Score';
    }
```

- Sample response from Plaid Sandbox environment

```bash
    {
        "endpoint": "/credit_score/plaid",
        "title": "Credit Score",
        "status_code": 200,
        "status": "success",
        "timestamp": "06-06-2022 20:48:02 GMT",
        "score": 401,
        "risk": {
            "loan_amount": 500,
            "risk_level": "medium"
        },
        "message": "Congrats! Your NEAR Oracle score is VERY POOR - 401 points. This score qualifies you for a short term loan of up to 93 NEAR which is equivalent to 500 USD over a recommended pay back period of 6 monthly installments Your total current balance is $320 USD across all accounts held with Chase NEARoracle found no credit card associated with your bank account. Credit scores rely heavily on credit card history. Improve your score by selecting a different bank account which shows credit history.",
        "feedback": {
            "score": {
                "score_exist": true,
                "points": 401,
                "quality": "very poor",
                "loan_amount": 500,
                "loan_duedate": 6,
                "card_names": null,
                "cum_balance": 320,
                "bank_accounts": 2
            },
            "advice": {
                "credit_exist": false,
                "credit_error": true,
                "velocity_error": true,
                "stability_error": false,
                "diversity_error": false
            }
        }
    }
```

## **Errors**

Note that error returns do not have `score` or `feedback` keys. The error description will appear under the message key.

Sample error response from Plaid Sandbox environment

```bash
    {
        'endpoint': '/credit_score/plaid',
        'message': 'invalid client_id or secret provided',
        'status': 'error',
        'status_code': 400,
        'timestamp': '03-22-2022 17:56:19 GMT',
        'title': 'Credit Score'
    }
```

## [NEAR WALLET](https://wallet.near.org/) : credit score model based on your NEAR wallet.

Coming soon.
