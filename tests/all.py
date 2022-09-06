#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from unittest import TestLoader, TextTestRunner, TestSuite

from hwtLib.tests.serialization.ipCorePackager_test import IpCorePackagerTC


def testSuiteFromTCs(*tcs):
    loader = TestLoader()
    loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
    suite = TestSuite(loadedTcs)
    return suite


suite = testSuiteFromTCs(
    IpCorePackagerTC
)

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=2)

    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallelTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallelTest = False

    if useParallelTest:
        # Run same tests across 4 processes
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests())
        runner.run(concurrent_suite)
    else:
        sys.exit(not runner.run(suite).wasSuccessful())
