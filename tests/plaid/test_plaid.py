from helpers.metrics_plaid import *
from helpers.helper import *
from config.helper import *
from datetime import datetime
import unittest
import json
import os


LOAN_AMOUNT = 10000
dummy_data = 'test_plaid.json'
json_file = os.path.join(os.path.dirname(__file__), dummy_data)


class PlaidFeedback:

    def __init__(self):
        configs = read_config_file(LOAN_AMOUNT)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['plaid']['scores']['models'])

        self.fb = create_feedback(models)
        self.fb['fetch'] = {}
        self.fb['diversity']['bank_name'] = 'TEST_BANK'


class PlaidParams:

    def __init__(self):
        configs = read_config_file(LOAN_AMOUNT)
        score_range = configs['score_range']
        params = configs['minimum_requirements']['plaid']['params']
        thresholds = configs['minimum_requirements']['plaid']['thresholds']

        self.prm = plaid_params(params, score_range)
        self.prd = thresholds['transactions_period']


class PlaidMetadata:

    def __init__(self):
        with open(json_file) as f:
            dataset = json.load(f)

        for d in dataset['transactions']:
            d.update(
                (k, datetime.strptime(v, '%Y-%m-%d').date())
                for k, v in d.items()
                if k == 'date'
            )

        transactions = dataset['transactions']
        accounts = remove_key_dupes(dataset['accounts'], 'account_id')
        data = format_plaid_data(transactions, accounts)

        credit_card = filter_dict(data, 'type', 'credit')
        checking = filter_dict(data, 'subtype', 'checking')
        savings = filter_dict(data, 'subtype', 'savings')

        metadata = {
            'credit_card': {
                'general': {},
                'util_ratio': {},
                'late_payment': {}
            },
            'checking': {
                'general': {},
                'income': {},
                'expenses': {},
                'investments': {
                    'earnings': {},
                    'deposits': {},
                    'withdrawals': {}
                }
            },
            'savings': {
                'general': {},
                'earnings': {},
                'cash_flow': {
                    'deposits': {},
                    'withdrawals': {}
                }
            }
        }

        if credit_card:
            credit_card = dict_reverse_cumsum(credit_card, 'amount', 'current')
            metadata = general(metadata, credit_card, 'credit_card')
            metadata = late_payment(metadata, credit_card)

        if checking:
            checking = dict_reverse_cumsum(checking, 'amount', 'current')
            metadata = general(metadata, checking, 'checking')
            metadata = income(metadata, checking, 'sub_category', 'payroll')
            metadata = expenses(metadata, checking, 'sub_category', 'rent')
            metadata = expenses(metadata, checking, 'sub_category', 'insurance')
            metadata = expenses(metadata, checking, 'sub_category', 'utilities')
            metadata = expenses(metadata, checking, 'sub2_category', 'loans and mortgages')
            metadata = investments(metadata, checking, 'sub2_category', 'financial planning and investments')

        if savings:
            savings = dict_reverse_cumsum(savings, 'amount', 'current')
            metadata = general(metadata, savings, 'savings')
            metadata = cash_flow(metadata, savings, 'category', 'interest')
            metadata = earnings(metadata, savings, 'sub_category', 'interest earned')

        self.mtd = metadata


# -------------------------------------------------------------------------- #
#                      some state-based UNIT TEST CASES                      #
#                - test core functions of Plaid algorithm -                  #
# -------------------------------------------------------------------------- #


class TestMetricCredit(unittest.TestCase):

    def setUp(self):
        ''' import test values (inputs) that will feed app functions '''

        # expected result
        self.expected = [1, 0.69, 1.0, 0.17, 0.38, 1, 0, 1]

        # inputs
        self.fb = PlaidFeedback().__dict__['fb']
        self.prm = PlaidParams().__dict__['prm']
        self.prd = PlaidParams().__dict__['prd']
        self.mtd = PlaidMetadata().__dict__['mtd']

    def tearDown(self):
        ''' reset test values after running tests'''

        self.fb = None
        self.prm = None
        self.prd = None
        self.mtd = None

    def test_credit(self):
        ''' perform test calling app functions '''

        s, f = plaid_credit_metrics(self.fb, self.prm, self.mtd, self.prd)

        self.assertCountEqual(s, self.expected)
        self.assertListEqual(s, self.expected)


class TestMetricVelocity(unittest.TestCase):

    def setUp(self):
        ''' import test values (inputs) that will feed app functions '''

        # expected result
        self.expected = [0, 0, 0, 1.0, 0.17]

        # inputs
        self.fb = PlaidFeedback().__dict__['fb']
        self.prm = PlaidParams().__dict__['prm']
        self.mtd = PlaidMetadata().__dict__['mtd']

    def tearDown(self):
        ''' reset test values after running tests'''

        self.fb = None
        self.prm = None
        self.mtd = None

    def test_velocity(self):
        ''' perform test calling app functions '''

        s, f = plaid_velocity_metrics(self.fb, self.prm, self.mtd)

        self.assertCountEqual(s, self.expected)
        self.assertListEqual(s, self.expected)


class TestMetricStability(unittest.TestCase):

    def setUp(self):
        ''' import test values (inputs) that will feed app functions '''

        # expected result
        self.expected = [0.17, 0.31]

        # inputs
        self.fb = PlaidFeedback().__dict__['fb']
        self.prm = PlaidParams().__dict__['prm']
        self.mtd = PlaidMetadata().__dict__['mtd']

    def tearDown(self):
        ''' reset test values after running tests'''

        self.fb = None
        self.prm = None
        self.mtd = None

    def test_stability(self):
        ''' perform test calling app functions '''

        s, f = plaid_stability_metrics(self.fb, self.prm, self.mtd)

        self.assertCountEqual(s, self.expected)
        self.assertListEqual(s, self.expected)


class TestMetricDiversity(unittest.TestCase):

    def setUp(self):
        ''' import test values (inputs) that will feed app functions '''

        # expected result
        self.expected = [0.9, 0.17]

        # inputs
        self.fb = PlaidFeedback().__dict__['fb']
        self.prm = PlaidParams().__dict__['prm']
        self.mtd = PlaidMetadata().__dict__['mtd']

    def tearDown(self):
        ''' reset test values after running tests'''

        self.fb = None
        self.prm = None
        self.mtd = None

    def test_diversity(self):
        ''' perform test calling app functions '''

        s, f = plaid_diversity_metrics(self.fb, self.prm, self.mtd)

        self.assertCountEqual(s, self.expected)
        self.assertListEqual(s, self.expected)
