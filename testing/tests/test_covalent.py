from support.metrics_covalent import * 
from config.helper import *
from support.helper import *
from datetime import datetime
import unittest
import json
import os


LOAN_AMOUNT = 24000
dummy_data = 'test_covalent.json'

json_file = os.path.join(os.path.dirname(
    __file__).replace('/tests', '/data'), dummy_data)

# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
#                - test core functions of Covalent algorithm -               #
# -------------------------------------------------------------------------- #

class TestMetricCredibility(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_credibility_kyc(self):
        pass

    def test_credibility_oldest_txn(self):
        pass



class TestMetricWealth(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_wealth_capital_now(self):
        pass

    def test_wealth_capital_now_adjusted(self):
        pass

    def test_wealth_volume_per_txn(self):
        pass




class TestMetricTraffic(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_traffic_cred_deb(self):
        pass

    def test_traffic_dustiness(self):
        pass

    def test_traffic_running_balance(self):
        pass

    def test_traffic_frequency(self):
        pass



class TestMetricStamina(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_stamina_methods_count(self):
        pass

    def test_stamina_coins_count(self):
        pass

    def test_stamina_dexterity(self):
        pass

    def test_stamina_loan_duedate(self):
        pass



class TestCovHelperFunctions(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_swiffer_duster(self):
        pass

    def test_purge_portfolio(self):
        pass

    def test_top_erc_only(self):
        pass

    def test_covalent_kyc(self):
        pass



class TestParametrizeCovalent(unittest.TestCase):

    def SetUp(self):
        pass

    def TearDown(self):
        pass

    def test_output_good(self):
        pass

    def test_output_empty(self):
        pass