<p align="center">
  <a href="https://near.org/">
    <img alt="NearMonotoneWhite" src="https://github.com/BalloonBox-Inc/near-oracle-contracts/blob/dev/images/monotone-black.png" width="550" />
  </a>
</p>

## NearOracle Credit Score Model :8ball: :chess_pawn: :spades:

### Algorithm Architecture

Understand the credit score model at a glance.
There are three distinct models, one for each of our chosen validators, namely Plaid, Coinbase & MetaMask.

**Plaid** model (powered by [Plaid](./images/logic_plaid.png))

- :curling_stone: analyze up to 5 years of transaction history
- :gem: dynamically select user's best credit card products
- :dart: detect recurring deposits and withdrawals (monthly)
- :hammer_and_wrench: deploy linear regression on minimum running balance over the past 24 months
- :magnet: auto-filter & discard microtransactions
- :pushpin: inspect loan, investment, and saving accounts

**Coinbase** model (powered by [Coinbase](./images/logic_coinbase.png))

- :bell: check for user KYC status
- :key: live fetch of top 25 cryptos by market cap via [CoinMarketCap](https://coinmarketcap.com/) API
- :fire: dynamically select user's best crypto wallets
- :closed_lock_with_key: auto-convert any currency to USD in real-time
- :bulb: analyze all transactions since Coinbase account inception
- :moneybag: compute user's net profit

**MetaMask** model (powered by [Covalent](./images/logic_covalent.png))

- :fox_face: authenticate user via MetaMask
- :parachute: account for credits, debits transactions, transfers, frequency, the cumulative balance now, and more
- :chains: fetch up to 100 top ERC20 tokens (by market capitalization) via [CoinMarketCap](https://coinmarketcap.com/) API
- :bar_chart: analyze time series of latest 400 transactions on MetaMask wallet
- :lady_beetle: inspect historical OHLCV for last 30 days

### Interpret Your Score

NarOracle returns to the user a numerical score ranging from 300-900 points. The score is partitioned into categorical bins </br> (`very poor` | `poor` | `fair` | `good` | `very good` | `excellent` | `exceptional`), which describe the score qualitatively (see fuel gauge in the diagram below). Every bin is associated with a USD equivalent, which represents the maximum loan amount in USD that a user qualifies for, based on the NearOracle calculation. Lastly, the NearOracle also returns the estimated payback period, namely the expected time it will take for the user to pay back the loan.

The loan terms (loan amount, qualitative descriptor, and payback period) are algorithmic recommendations, and, therefore, they are not prescriptive. Although we strongly advise lenders and borrowers to consider NearOracle's parameters, we also encourage them to stipulate loan terms that best suit their unique needs.

![](./images/credit_score_range.png)

---

## Clone This Project :key: :lock: :package:

### 1. Clone locally

Download or clone the repo to your machine, running in terminal

```bash
git clone  ... my-project-name
cd my-project-name
```

### 2. Install dependencies

Run either of the commands below. You'll need either `pip` or `conda` package manager

```bash
pip install -r requirements.txt                                 # using pip
conda create --name <env_name> --file requirements.txt          # using Conda
```

### 3. Environment variables

Create a `.env` local file in your root folder. The required credentials are

```bash
PLAID_ENV='sandbox'
DATABASE_URL='postgres_url'
```

### 4. Execute locally

If you want to test the algorithm alone in the backend (independently from the dApp frontend) we recommend you do so using the Swagger API platform. Running the commands below will redirect you to the Swagger, where you'll be able to run _in the backend_ trial credit score calculations for your preferred validator (Plaid, Coinbase, or Covalent)

```bash
cd my-project-name
uvicorn main:app –reload
```

> :warning: The oracle will execute properly, only if you set up a correct and complete `.env` file. <br/>
> :radioactive: depending on the validator you choose you'll need to enter the parameters for the API endpoint request.

Procure the necessary keys here:

- CoinMarketCap API key &#8594; follow the Developers guide [here](https://coinmarketcap.com/api/documentation/v1/#section/Introduction)
- Plaid client_id and secret_key &#8594; create a Plaid account [here](https://dashboard.plaid.com/signin), then retrieve your Plaid [keys](https://dashboard.plaid.com/team/keys)
- Coinbase API Key &#8594; create a Coinbase account [here](https://www.coinbase.com/signup), then retrieve your Coinbase [keys](https://www.coinbase.com/settings/api) </br>
  To generate a new set of API keys follow this flow: `Coinbase` -> `settings` -> `API` -> `New API Key`.
- Covalent API key &#8594; register [here](https://www.covalenthq.com/platform/#/auth/register/)