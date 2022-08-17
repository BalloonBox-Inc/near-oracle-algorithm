# 🔮 NEAR Oracle

<p align="center">
  <a href="https://near.org/">
    <img alt="NearMainLogo" src="https://github.com/BalloonBox-Inc/NEARoracle-Oracle/blob/dev/images/logo_near_oracle.png" width="700" />
  </a>
</p>

## At a Glance

NearOracle is an oracle for credit scoring designed for the web3 community. The oracle returns a numerical score affirming users' credibility and trustworthiness in the web3 space. The dApp was designed with one specific use case in mind: unsecured P2P lending: facilitating lending and borrowing of crypto loans.

The dApp works as follow:

- it acquires user's financial data by integrating with three validators ([Plaid](https://dashboard.plaid.com/overview), [Coinbase](https://developers.coinbase.com/), and [Covalent](https://www.covalenthq.com/))
- it runs a credit scoring algorithm on given data to compute a score representing the financial health of a user
- it writes the score to the NEAR Protocol blockchain via a Wasm smart contract build using the Rust `NEAR SDK`

Ultimately, this will incentivize on-chain traffic, it will affirm the reputation of those users requesting a credit score, and it will execute a credit score check to validate their credibility, while also preserving their privacy.

---

## This Repo

This GitHub repo contains the codebase of the NearOracle credit score algorithm. The code features 3 validators, 4 API integrations, 12 score metrics, and 25+ functions to calculate users' credit scores. The front end of the NearOracle DApp, after fetching the user's data, passes it to the algorithm to execute and return a score. The Rust smart contract is stored at the [near-oracle-contract](https://github.com/BalloonBox-Inc/near-oracle-contract) repo.

## Execute Locally

- download or clone the repo to your machine
- install dependancies
- set up `.env` file
- execute

### Package Manager Required :package:

pip or conda

Run in local terminal the following command:

```bash
git clone  ... my-project-name
cd my-project-name
```

Run _either_ of the command below to install dependencies:

```bash
pip install -r requirements.txt                                 # using pip
conda create --name <env_name> --file requirements.txt          # using Conda
```

### Credentials Required :old_key: :lock:

If you want to test the algorithm alone (independently from the dApp frontend), then continue reading this page and follow the step-by-step guide below. You'll need to create a Developer CoinMarketCap API Key, following the CoinMarketCap Developers guide [here](https://coinmarketcap.com/api/documentation/v1/#section/Introduction). In addition, you'll need either a Plaid account, Coinbase account, or MetaMask wallet. If you don't own one yet, you can create an account [here](https://dashboard.plaid.com/signin) and [here](https://www.coinbase.com/signup), respectively and then retrieve your Plaid [keys](https://dashboard.plaid.com/team/keys) and your Coinbase [keys](https://www.coinbase.com/settings/api). For Coinbase, you'll need to generate a new set of API keys. Do so, following this flow: `Coinbase` -> `settings` -> `API` -> `New API Key`.

Next, create a `.env` local file in your root folder:

```bash
PLAID_ENV='sandbox'
DATABASE_URL='postgres_url'
```

### Run Locally

`cd` into the local directory where you cloned NEARoracle_Oracle. To run the credit score algorithm locally as a stand-alone Python project execute this command in terminal. You must also ensure you are in your project root.

```bash
cd my-project-name
python demo1.0.py
```
> :warning: The oracle will execute properly, only if you set up a correct and complete `.env` file.

## Credit Score Model

### Algorithm Architecture :page_facing_up:

Understand the credit score model at a glance.

There are three distinct models, one for each of our chosen validators, namely Plaid, Coinbase & Covalent.

[**Plaid model**](./images/logic_plaid.png) diagram and features:

- :curling_stone: analyze 5 years of transaction history
- :gem: dynamically select user's best credit card products
- :dart: detect recurring deposits and withdrawals (monthly)
- :hammer_and_wrench: deploy linear regression on minimum running balance over the past 24 months
- :magnet: auto-filter & discard micro transactions
- :pushpin: inspect loan, investment, and saving accounts

[**Coinbase model**](./images/logic_coinbase.png) diagram and features:

- :bell: check for user KYC status
- :key: live fetch of top 25 cryptos by market cap via [CoinMarketCap](https://coinmarketcap.com/) API
- :fire: dynamically select user's best crypto wallets
- :closed_lock_with_key: auto-convert any currency to USD in real-time
- :bulb: analyze all transactions since Coinbase account inception
- :moneybag: compute user's net profit

[**Covalent model**](./images/logic_covalent.png) diagram and features:

- :fox_face: authenticate user via MetaMask 
- :parachute: account for credits, debits transactions, transfers, frequency, cumulative balance now, and more
- :chains: fetch up to 100 top ERC20 tokens (by market capitalization) via [CoinMarketCap](https://coinmarketcap.com/) API
- :bar_chart: analyze time series of latest 400 transactions on MetaMask wallet
- :chart: inspect historical OHLCV for last 30 days


## Interpret Your Score :mag:

NarOracle returns to the user a numerical score ranging from 300-900 points. The score is partitioned into categorical bins (very poor | poor | fair | good | very good | excellent | exceptional), which describe the score qualitatively (see fuel gauge in the diagram below). Every bin is associated with a USD equivalent, which represents the maximum loan amount in USD that a user qualifies for, based on the NearOracle calculation. Lastly, the NearOracle also returns the estimated payback period, namely the expected time it will take for the user to pay back the loan. The loan terms (loan amount, qualitative descriptor, and payback period) are algorithmic recommendations, and, therefore, they are not prescriptive. Although we strongly advise lenders and borrowers to consider the NearOracle's parameters, we also encourage them to stipulate loan terms to best suit their needs.
![](./images/credit_score_range.png)

### Unit tests :page_facing_up:

The algorithm has undergone extensive unit testing. To execute these tests yourself, run the following command in terminal, from the root folder of this Git repo:

```bash
python -m unittest -v unit_tests                # for both Plaid, Coinbase, and Covalent
```

> :warning: `unittest` relies on imported test data (_json_ files). We crafted some fake and anonimized test data-sets with the explicit goal of executing unit tests. Find these two data sets in the `tests` directory.
