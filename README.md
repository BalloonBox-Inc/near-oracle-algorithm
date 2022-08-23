<p align="center">
  <a href="https://near.org/">
    <img alt="Near" src="https://github.com/BalloonBox-Inc/near-oracle-algorithm/blob/dev/images/logo_NearOracle.png" width="700" />
  </a>
</p>

## Credit Scoring on NEAR Protocol 🔮 :ringed_planet: :mag:

NearOracle is an oracle for credit scoring that runs on the NEAR protocol and serves web3 users interested in lending or borrowing money in the crypto space. This repo contains the Python codebase of the credit scoring algorithm used by the NearOracle dApp, a dApp that BalloonBox developed through a grant by the [NEAR Foundation](https://near.foundation/). The oracle reads in the user's fiat or crypto financial history and uses it to calculate a numerical score, namely an integer representing a user's financial health. Ranking users through a credit score is essential to distinguish between trusted and suspicious agents in the web3 space. The dApp caters to a specific use case, namely unsecured P2P lending: facilitating lending and borrowing of crypto loans.

###### How does the dApp work?

- it acquires user's financial data by integrating with three validators ([Plaid](https://dashboard.plaid.com/overview), [Coinbase](https://developers.coinbase.com/), and [MetaMask](https://metamask.io/))
- it runs the credit scoring algorithm to compute a score assessing a user's financial health
- it writes the score to the blockchain via a Wasm smart contract build using the Rust `NEAR SDK`

###### In this Repo

This GitHub repo contains the codebase of the NearOracle credit score algorithm. The code features 3 validators, 4 API integrations, 12 score metrics, and 25+ functions to calculate users' credit scores. The front end of the NearOracle dApp (see codebase at [`near-oracle-client`](https://github.com/BalloonBox-Inc/near-oracle-client)), after fetching the user's data, passes it to the algorithm, which executes and returns a score via a Rust smart contract (see codebase at [`near-oracle-contract`](https://github.com/BalloonBox-Inc/near-oracle-contract)).

Continue to read these docs to understand the algorithm or clone this project and spin it up in your local machine.

---


### :octopus: Directory Structure
The tree diagram below describes the structure of this Git Repo. Notice that the decision tree only features the most important files and disregards all others.

```bash
.
└───
    ├── config
    │   └── config.json               #contains all model parameters and weights - tune this file to alter the model
    ├── helpers
    │   ├── feedback.py               #string formatter returning a qualitative score feedback
    │   ├── helper.py                 #helper functions for data cleaning
    │   ├── metrics_coinbase.py       #logic to analyze a user's Coinbase account data
    │   ├── metrics_covalent.py       #logic to analyze a user's ETH wallet data (powered by Covalent)
    │   ├── metrics_plaid.py          #logic to analyze a user's bank account data (powered by Plaid)
    │   ├── models.py                 #aggregre the granular credit score logic into 4 metrics
    │   ├── risk.py                   #high/med/low risk indicators
    │   ├── score.py                  #aggregate score metrics into an actual credit score
    │   └── README.md                 #docs on credit score model & guideline to clone project
    ├── market
    │   └── coinmarketcap.py          #hit a few endpoints on Coinmarketcap (live exchange rate & top cryptos)
    ├── routers
    │   ├── coinbase.py               #core execution logic - Coinbase
    │   ├── covalent.py               #core execution logic - Covalent
    │   ├── kyc.py                    #core execution logic - KYC template
    │   ├── plaid.py                  #core execution logic - Plaid
    │   └── README.md                 #docs on the API endpoints
    ├── support
    │   ├── assessment.py             #auto generates from Cargo.toml
    │   ├── crud.py                   #Create, Read, Update, Delete (CRUD) - database handler
    │   ├── database.py               #set up PostgreSQL database to store computed scores
    │   ├── models.py                 #clases with data to enter in new row of database
    │   └── schemas.py                #http request classes
    ├── tests
    │   ├── coinbase                  #directory with 2 files: Coinbase pytests & dummy test data json
    │   ├── covalent                  #directory with 2 files: Covalent pytests & dummy test data json
    │   └── plaid                     #directory with 2 files: Plaid pytests & dummy test data json
    ├── validator
    │   ├── coinbase.py               #functions calling Coinbase API
    │   ├── covalent.py               #functions calling Covalent API
    │   └── plaid.py                  #functions calling Plaid API
    ├── LICENCE
    ├── main.py                       #core file - handle API calls, directing them to the router folder
    ├── Procfile                      #set up uvicorn app in Heroku
    ├── pytest.ini                    #???
    ├── README.md                     #this landing page
    └── requirements.txt              #Pyhon module required to run this project
```