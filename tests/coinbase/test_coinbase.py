from helpers.metrics_coinbase import *
from config.helper import *
from helpers.helper import *
from datetime import datetime
import unittest
import json
import os


LOAN_AMOUNT = 10000
dummy_data = 'test_coinbase.json'

json_file = os.path.join(os.path.dirname(__file__), dummy_data)

# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                                                            #
# -------------------------------------------------------------------------- #


def str_to_date(acc, feedback):
    '''
    Description:
        serialize a Python data structure converting string instances into datetime objects

    Parameters:
        tx (list): locally stored Coinbase data. Either account OR transactions data

    Returns:
        all_txn (list): serialized list containing user accounts OR transactions. String dates are converted to datetime objects
    '''
    try:
        converted = []
        for x in acc:
            if x['created_at']:
                x['created_at'] = datetime.strptime(
                    x['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
                converted.append(x)

        return converted

    except Exception as e:
        feedback['kyc'][str_to_date.__name__] = str(e)


# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
#                - test core functions of Coinbase algorithm -               #
# -------------------------------------------------------------------------- #

class TestMetricsCoinbase(unittest.TestCase):

    # factor out set-up code implementing the setUp() method
    def setUp(self):

        # import variables from config.json
        configs = read_config_file(LOAN_AMOUNT)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])
        self.fb = create_feedback(models)

        with open(json_file) as f:
            self.acc = str_to_date(json.load(f)['accounts'], self.fb)
        with open(json_file) as f:
            self.tx = json.load(f)['transactions']

        # import parameters
        score_range = configs['score_range']
        params = configs['minimum_requirements']['coinbase']['params']
        self.par = coinbase_params(params, score_range)

    # clean up code at the end of this test class

    def tearDown(self):
        self.fb = None
        self.acc = None
        self.tx = None
        self.par = None

    def test_kyc(self):
        '''
        - ensure the output is always a tuple (int, dict)
        - ensure the output is never NoneType, even when parsing NoneTypes
        - ensure returns full score of 1 when good args are passed to the fn
        '''
        bad_fb = {'history': {}, 'liquidity': {}, 'activity': {}}
        badkyc = kyc(None, None, bad_fb)

        self.assertIsInstance(badkyc, tuple)
        self.assertIsInstance(badkyc[0], int)
        self.assertIsInstance(badkyc[1], dict)
        self.assertIsNotNone(kyc(None, None, None))
        self.assertEqual(kyc(self.acc, self.tx, self.fb)[0], 1)

    def test_history_acc_longevity(self):
        '''
        - variable 'age' should be a non-negative of type: int or float
        - if there's no account, the score should be 0
        '''
        history_acc_longevity(self.acc, self.fb, self.par)

        self.assertGreaterEqual(history_acc_longevity.age, 0)
        self.assertIsInstance(history_acc_longevity.age, (int, float))
        self.assertEqual(history_acc_longevity([], self.fb, self.par)[0], 0)

    def test_liquidity_tot_balance_now(self):
        '''
        - empty account should result in 'no balance' error
        '''
        self.assertRegex(liquidity_tot_balance_now([], self.fb, self.par)[
                         1]['liquidity']['error'], 'no balance')

    def test_liquidity_loan_duedate(self):
        '''
        - duedate should be at most 6 months
        - this is the only function that returns no score, but rather, it returns only the feedback dict
        '''
        self.assertLessEqual(liquidity_loan_duedate(self.tx, self.fb, self.par)[
                             'liquidity']['loan_duedate'], 6)
        self.assertIsInstance(liquidity_loan_duedate(self.tx, self.fb, self.par), dict)

    def test_liquidity_avg_running_balance(self):
        '''
        - no tx yields a 'no tx' error
        '''
        self.assertRegex(liquidity_avg_running_balance(self.acc, [], self.fb, self.par)[
                         1]['liquidity']['error'], 'no transaction history')

    def test_activity_tot_volume_tot_count(self):
        '''
        - tot_volume should be of type int or float
        - tot_volume should be non-negative
        - credit and debit checks share the same dictionary key
        - no tx returns 'no tx history' error
        '''
        fb = {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}
        cred, cred_fb = activity_tot_volume_tot_count(self.tx, 'credit', fb, self.par)
        deb, deb_fb = activity_tot_volume_tot_count(self.tx, 'debit', fb, self.par)

        for a in [cred, deb]:
            self.assertIsInstance(a, (float, int))
            self.assertGreaterEqual(a, 0)

        self.assertEqual(cred_fb['activity'].get(
            'credit').keys(), deb_fb['activity'].get('debit').keys())
        self.assertRegex(activity_tot_volume_tot_count([], 'credit', self.fb, self.par)[
                         1]['activity']['error'], 'no transaction history')

    def test_activity_consistency(self):
        '''
        - ensure you've accounted for all registered txns
        - ensure txn dates are of Type datetime (perform Type check on randomly chosen date)
        - avg volume should be a positive number
        - no tx returns 'no tx history' error
        '''
        a, b = activity_consistency(self.tx, 'credit', self.fb, self.par)
        i = list(activity_consistency.frame.index)
        d = [x[0] for x in activity_consistency.typed_txn]

        self.assertCountEqual(i, d)
        self.assertIsInstance(np.random.choice(d), datetime)
        self.assertGreater(a, 0)
        self.assertRegex(activity_consistency([], 'credit', self.fb, self.par)[
                         1]['activity']['error'], 'no transaction history')

    def test_activity_profit_since_inception(self):
        '''
        - 'profit' variable should be a float or int
        - 'profit' should be positive
        - if there's no profit, then should raise an exception
        '''
        activity_profit_since_inception(self.acc, self.tx, self.fb, self.par)

        self.assertIsInstance(
            activity_profit_since_inception.profit, (float, int))
        self.assertGreater(activity_profit_since_inception.profit, 0)
        self.assertRegex(activity_profit_since_inception([], [], self.fb, self.par)[
                         1]['activity']['error'], 'no net profit')

    def test_net_flow(self):
        '''
        - output should be of type tuple(DataFrame, dict)
        - bad input parameters should raise and exception
        '''
        a = net_flow(self.tx, 12, self.fb)
        b = net_flow([], 6, self.fb)
        c = net_flow(None, 6, {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}})

        # good inputs
        self.assertIsInstance(a, tuple)
        self.assertIsInstance(a[0], pd.core.frame.DataFrame)
        self.assertIsInstance(a[1], dict)

        # bad inputs
        self.assertEqual(len(b[0]), len(c[0]))
        self.assertRegex(b[1]['liquidity']['error'], 'no consistent net flow')
        self.assertRegex(c[1]['liquidity']['error'],
                         "'NoneType' object is not iterable")


# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
#            - run same tests, passing different values each time -          #
#                    - and expecting the same result -                       #
# -------------------------------------------------------------------------- #

class TestParametrizeCoinbase(unittest.TestCase):
    '''
    The TestParametrizeOutput object checks that ALL functions
    of our Coinbase algorithm ALWAYS return a tuple comprising of:
    - an int (i.e., the score)
    - a dict (i.e., the feedback)
    It also checks that the score is ALWAYS in the range [0, 1]
    Finally, it checks that even when all args are NoneTypes, th output is still a tuple
    '''

    def setUp(self):
        # import variables from config.json
        configs = read_config_file(LOAN_AMOUNT)
        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])
        self.fb = create_feedback(models)

        with open(json_file) as f:
            self.acc = str_to_date(json.load(f)['accounts'], self.fb)
        with open(json_file) as f:
            self.tx = json.load(f)['transactions']

        # import parameters
        score_range = configs['score_range']
        params = configs['minimum_requirements']['coinbase']['params']
        self.par = coinbase_params(params, score_range)

        self.args = {
            'good':
            [
                [self.acc, self.tx, self.fb],
                [self.acc, self.fb, self.par],
                [self.acc, self.tx, self.fb, self.par],
                [self.acc, self.fb, self.par],
                [self.tx, 'credit', self.fb, self.par],
                [self.tx, 'debit', self.fb, self.par],
                [self.tx, 'credit', self.fb, self.par],
                [self.tx, 'debit', self.fb, self.par],
                [self.acc, self.tx, self.fb, self.par]
            ],
            'empty':
            [
                [[], None, self.fb],
                [None, self.fb, self.par],
                [[], [], self.fb, self.par],
                [None, self.fb, self.par],
                [[], None, self.fb, self.par],
                [[], [], self.fb, self.par],
                [[], None, self.fb, self.par],
                [None, [], self.fb, self.par],
                [None, None, self.fb, self.par]
            ]
        }

        self.fn = {
            'all': [
                kyc,
                history_acc_longevity,
                liquidity_avg_running_balance,
                liquidity_tot_balance_now,
                activity_consistency,
                activity_consistency,
                activity_tot_volume_tot_count,
                activity_tot_volume_tot_count,
                activity_profit_since_inception
            ]
        }

    def tearDown(self):
        for y in [self.fb, self.acc, self.tx, self.par, self.args, self.fn]:
            y = None

    def test_output_good(self):
        for (f, a) in zip(self.fn['all'], self.args['good']):
            x = f(*a)
            with self.subTest():
                self.assertIsInstance(x, tuple)
                self.assertLessEqual(x[0], 1)
                self.assertIsInstance(x[0], (float, int))
                self.assertIsInstance(x[1], dict)

    def test_output_empty(self):
        for (f, a) in zip(self.fn['all'], self.args['empty']):
            x = f(*a)
            with self.subTest():
                self.assertIsInstance(x, tuple)
                self.assertEqual(x[0], 0)
                self.assertIsInstance(x[0], (float, int))
                self.assertIsInstance(x[1], dict)
