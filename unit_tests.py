from tests.test_coinbase import *
from tests.test_covalent import *
# from tests.test_plaid import *
import unittest


# Run the actual tests bundling classes of test cases into test suites
def suite():
    suite = unittest.TestSuite()

    # Plaid
    # suite.addTest(unittest.makeSuite(TestMetricCredit))
    # suite.addTest(unittest.makeSuite(TestMetricVelocity))
    # suite.addTest(unittest.makeSuite(TestMetricStability))
    # suite.addTest(unittest.makeSuite(TestMetricDiversity))
    # suite.addTest(unittest.makeSuite(TestHelperFunctions))
    # suite.addTest(unittest.makeSuite(TestParametrizePlaid))

    # Coinbase
    suite.addTest(unittest.makeSuite(TestMetricsCoinbase))
    suite.addTest(unittest.makeSuite(TestParametrizeCoinbase))

    # Covalent
    suite.addTest(unittest.makeSuite(TestMetricCredibility))
    suite.addTest(unittest.makeSuite(TestMetricWealth))
    suite.addTest(unittest.makeSuite(TestMetricTraffic))
    suite.addTest(unittest.makeSuite(TestMetricStamina))
    suite.addTest(unittest.makeSuite(TestCovHelperFunctions))
    suite.addTest(unittest.makeSuite(TestParametrizeCovalent))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
