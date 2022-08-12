from helpers.metrics_covalent import *
from config.helper import *
from helpers.helper import *
import unittest
import json
import os


ERC_RANK = {'ETH': 2, 'USDT': 3, 'USDC': 4, 'MATIC': 11, 'CRO': 22, 'LINK': 23, 'TUSD': 45,
            'MKR': 49, 'HT': 60, 'BAT': 68, 'ENJ': 77, 'HOT': 92, 'NEXO': 94, 'WETH': 2.5}
LOAN_AMOUNT = 24000
dummy_data = 'test_covalent.json'

json_file = os.path.join(os.path.dirname(__file__), dummy_data)

# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
#                - test core functions of Covalent algorithm -               #
# -------------------------------------------------------------------------- #


class TestMetricCredibility(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']

    def tearDown(self):
        # post-test cleanup
        self.fb = None
        self.txn = None
        self.bal = None
        self.parm = None

    def test_credibility_kyc(self):
        # should return a binary score 0|1
        pass_kyc = credibility_kyc(self.txn, self.bal, self.fb)
        fail_kyc = credibility_kyc(None, self.bal, self.fb)
        self.assertEqual(pass_kyc[0], 1)
        self.assertEqual(fail_kyc[0], 0)

    def test_credibility_oldest_txn(self):
        # full marks for wallets older than 9 months
        length = credibility_oldest_txn(
            self.txn,
            self.fb,
            self.parm
        )

        if length[1]['credibility']['longevity_days'] >= 270:  # days
            self.assertEqual(length[0], 1)

        self.assertRaises(
            Exception,
            credibility_oldest_txn,
            ({}, self.fb, self.parm)
        )


class TestMetricWealth(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']

    def tearDown(self):
        # post-test cleanup
        self.fb = None
        self.txn = None
        self.bal = None
        self.parm = None

    def test_wealth_capital_now(self):
        # cumulative capital now should match the sum of all balances now
        tot = sum([b['quote'] for b in self.bal['items']])
        tot_bal = wealth_capital_now(
            self.bal, self.fb, self.parm
        )

        self.assertEqual(int(tot_bal[1]['wealth']['cum_balance_now']), int(tot))
        self.assertIn('error', wealth_capital_now({},
                                                  self.fb,
                                                  self.parm)[1]['wealth']
                      )
        self.bal['quote_currency'] = 'EUR'
        self.assertRaises(
            Exception,
            wealth_capital_now,
            (self.bal, self.fb, self.parm)
        )

    def test_wealth_capital_now_adjusted(self):
        # keep only top-ranked ERC tokens
        a = wealth_capital_now_adjusted(
            self.bal,
            self.fb,
            ERC_RANK,
            self.parm
        )
        keep_erc = [b['contract_ticker_symbol'] for b in wealth_capital_now_adjusted.top['items']]
        for erc in keep_erc:
            self.assertIn(erc, list(ERC_RANK.keys()))
        self.assertGreater(a[1]['wealth']['cum_balance_now_adjusted'], 1000)

    def test_wealth_volume_per_txn(self):
        # ensure avg volume oer txn is calculated correctly
        voluminous_txns = [t for t in self.txn['items'] if t['successful'] and t['value_quote'] > 0]
        avg0 = sum(t['value_quote'] for t in self.txn['items']) / len(voluminous_txns)
        avg1 = wealth_volume_per_txn(
            self.txn,
            self.fb,
            self.parm
        )
        self.assertEqual(int(avg1[1]['wealth']['avg_volume_per_txn']), int(avg0))
        self.assertEqual(
            wealth_volume_per_txn({}, self.fb, self.parm)[0], 0)
        self.assertRaises(Exception, wealth_volume_per_txn, ({}, self.fb, {}, None))


class TestMetricTraffic(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']
        with open(json_file) as f:
            self.por = json.load(f)['portfolio']

    def tearDown(self):
        # post-test cleanup
        self.fb = None
        self.txn = None
        self.bal = None
        self.por = None
        self.parm = None

    def test_traffic_cred_deb(self):
        # ensure this function operates for both 'credit' and 'debit' checks
        out = traffic_cred_deb(
            self.txn,
            self.fb,
            'credit',
            self.parm
        )
        self.assertTrue('volume_credit_txns' in list(out[1]['traffic'].keys()))
        self.assertRaises(Exception, traffic_cred_deb, traffic_cred_deb(
            self.txn,
            self.fb,
            'swap',
            self.parm
        ), "you passed an invalid param: accepts only 'credit', 'debit', or 'transfer'")

    def test_traffic_dustiness(self):
        # when all txn are voluminous, the user should earn the max score of 1
        if len(swiffer_duster(self.txn, self.fb)['items']) == len(self.txn['items']):
            self.assertEqual(traffic_dustiness(self.txn, self.fb, self.parm)[0], 1)
        self.assertIn('error',
                      list(traffic_dustiness(self.bal, self.fb, self.parm)[1]['traffic'].keys())
                      )

    def test_traffic_running_balance(self):
        # avg running balances calculated manuallya and algorithmically should be the same
        a = traffic_running_balance(
            self.por,
            self.fb,
            self.parm,
            ERC_RANK
        )
        quotes = [y['close']['quote'] for x in self.por['items'] for y in x['holdings']
                  if x['contract_ticker_symbol'] == traffic_running_balance.best_token]
        avg = sum(quotes) / len(quotes)
        self.assertEqual(int(a[1]['traffic']['avg_running_balance_best_token']), int(avg))

    def test_traffic_frequency(self):
        # score > 0.5 when monthly_txn_frequency > 0.5
        a = traffic_frequency(self.txn, self.fb, self.parm)
        frequency = float(a[1]['traffic']['txn_frequency'].split(' ')[0])
        if frequency > 0.5:
            self.assertGreater(a[0], 0.5)
        if self.txn['items']:
            self.assertGreater(frequency, 0)


class TestMetricStamina(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']
        with open(json_file) as f:
            self.por = json.load(f)['portfolio']

    def tearDown(self):
        # post-test cleanup
        self.fb = None
        self.txn = None
        self.bal = None
        self.por = None
        self.parm = None

    def test_stamina_methods_count(self):
        # the function should detect all methods ever invoked by the user
        stamina_methods_count(
            self.txn,
            self.fb,
            self.parm
        )
        methods = list(set([t['log_events'][0]['decoded']['name']
                            for t in self.txn['items'] if t['log_events']]))
        for m in methods:
            self.assertIn(m, list(stamina_methods_count.methods.keys()))

    def test_stamina_coins_count(self):
        # ensure the function detects all legitimate coins owned by the user
        stamina_coins_count(
            self.bal,
            self.fb,
            self.parm,
            ERC_RANK
        )
        coins = [c['contract_ticker_symbol'] for c in self.bal['items']
                 if c['contract_ticker_symbol'] in list(ERC_RANK.keys()) and c['quote'] > 0]
        self.assertEqual(stamina_coins_count.unique_coins, len(coins))
        self.assertRaises
        (
            Exception,
            stamina_coins_count,
            (
                self.txn,
                self.fb,
                self.parm,
                ERC_RANK
            )
        )

    def test_stamina_dexterity(self):
        # count of smart trades should be an int
        smart_trades = stamina_dexterity(
            self.por,
            self.fb,
            self.parm,
        )
        self.assertIsInstance(smart_trades[1]['stamina']['count_smart_trades'], int)
        self.assertRaises(Exception, stamina_dexterity, ({}, self.fb, None, None, None))

    def test_stamina_loan_duedate(self):
        # payback period equates to length of txn history (give or take)
        longevity = credibility_oldest_txn(
            self.txn,
            self.fb,
            self.parm,
        )[1]['credibility']['longevity_days']
        duedate = stamina_loan_duedate(
            self.txn,
            self.fb,
            self.parm
        )['stamina']['loan_duedate']

        self.assertGreater(longevity/30, duedate)


class TestCovHelperFunctions(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)
        self.fb['fetch'] = {}

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']
        with open(json_file) as f:
            self.por = json.load(f)['portfolio']

    def tearDown(self):
        # post-test cleanup
        self.fb = None
        self.txn = None
        self.bal = None
        self.por = None
        self.parm = None

    def test_swiffer_duster(self):
        # ensure swiffer_duster() is removing all dusty txns
        length0 = len(self.txn['items'])
        dust = [t for t in self.txn['items'] if t['value_quote'] == 0]
        self.txn = swiffer_duster(self.txn, self.fb)
        for t in self.txn['items']:
            self.assertTrue(t['value_quote'] > 0)
        self.txn['quote_currency'] == 'YEN'
        self.assertRaises(Exception, swiffer_duster, (self.txn, self.fb))
        if len(dust) > 0:
            self.assertGreater(length0, len(self.txn['items']))

    def test_purge_portfolio(self):
        # ensure the purge occurs
        self.por['quote_currency'] == 'CAD'
        self.assertRaises(Exception, purge_portfolio, (self.por, self.fb))
        length0 = len(self.por['items'])
        self.por = purge_portfolio(self.por, self.fb)
        self.assertLess(len(self.por['items']), length0)

    def test_top_erc_only(self):
        # after skimming there should remian only legitimate erc tokens
        top_erc = list(ERC_RANK.keys())
        self.bal = top_erc_only(self.bal, self.fb, top_erc)
        self.por = top_erc_only(self.por, self.fb, top_erc)
        for b in self.bal['items']:
            self.assertIn(b['contract_ticker_symbol'], top_erc)
        for p in self.por['items']:
            self.assertIn(p['contract_ticker_symbol'], top_erc)

    def test_covalent_kyc(self):
        # ensure we verify only legitimate users
        self.assertTrue(covalent_kyc(self.txn, self.bal, self.por))
        self.txn['items'] = self.txn['items'][:5]
        self.assertFalse(covalent_kyc(self.txn, self.bal, self.por))
        self.assertRaises(Exception, covalent_kyc, (self.txn, None, self.por))

    def test_fetch_covalent(self):
        # if the input data is legitimate, there should be no JSONDecodeError
        a = fetch_covalent(self.txn, self.bal, self.por, self.fb)
        for x in [self.txn, self.bal, self.por]:
            self.assertIsInstance(x, dict)
            if x.keys():
                self.assertFalse(a['fetch']['JSONDecodeError'])


class TestParametrizeCovalent(unittest.TestCase):

    def setUp(self):

        # import model parameters from config.json
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        parm = configs['minimum_requirements']['covalent']['params']
        self.parm = covalent_params(parm, score_range)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['covalent']['scores']['models'])
        self.fb = create_feedback(models)

        # import data
        with open(json_file) as f:
            self.txn = json.load(f)['txn']
        with open(json_file) as f:
            self.bal = json.load(f)['balances']
        with open(json_file) as f:
            self.por = json.load(f)['portfolio']

        self.args1 = {
            'good':
            [
                [self.txn, self.bal, self.fb],
                [self.txn, self.fb],
                [self.bal, self.fb],
                [self.bal, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.txn, self.fb],
                [self.bal, self.fb],
                [self.por, self.fb],
            ],
            'incomplete':
            [
                [None, [], self.fb],
                [None, self.fb],
                [[], self.fb],
                [[], self.fb],
                [None, self.fb],
                [[], self.fb],
                [None, self.fb],
                [[], self.fb],
                [[], self.fb],
                [[], self.fb],
                [None, self.fb],
                [None, self.fb],
                [[], self.fb],
            ]
        }

        self.args2 = [
            list(),
            [self.parm],
            [self.parm],
            [ERC_RANK, self.parm],
            [self.parm],
            ['credit', self.parm],
            ['debit', self.parm],
            [self.parm],
            [self.parm, ERC_RANK],
            [self.parm],
            [self.parm],
            [self.parm, ERC_RANK],
            [self.parm],
        ]

        self.fn = {
            'all':
            [
                credibility_kyc,
                credibility_oldest_txn,
                wealth_capital_now,
                wealth_capital_now_adjusted,
                wealth_volume_per_txn,
                traffic_cred_deb,
                traffic_cred_deb,
                traffic_dustiness,
                traffic_running_balance,
                traffic_frequency,
                stamina_methods_count,
                stamina_coins_count,
                stamina_dexterity
            ]
        }

    def tearDown(self):
        # post-test cleanup
        for y in [self.txn, self.bal, self.por, self.parm, self.fb, self.args1, self.args2, self.fn]:
            y = None

    def test_output_good(self):
        for (f, a, b) in zip(self.fn['all'], self.args1['good'], self.args2):
            x = f(*a, *b)
            with self.subTest():
                self.assertLessEqual(x[0], 1)
                self.assertIsInstance(x, tuple)
                self.assertIsInstance(x[1], dict)
                self.assertIsInstance(x[0], (float, int))

    def test_output_incomplete(self):
        for (f, a, b) in zip(self.fn['all'], self.args1['incomplete'], self.args2):
            x = f(*a, *b)
            with self.subTest():
                self.assertLessEqual(x[0], 1)
                self.assertIsInstance(x, tuple)
                self.assertIsInstance(x[1], dict)
                self.assertIsInstance(x[0], (float, int))


if __name__ == '__main__':
    unittest.main()
