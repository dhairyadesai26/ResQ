"""
ResQ Web - Unified Test Runner
Discovers and executes all agent unit tests and backend integration tests.
Prints a comprehensive pass/fail summary mapping to formal OS test cases.
"""

import sys
import os
import unittest
import time

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


def main():
    print("=" * 70)
    print("  ResQ Web - Operating Systems Verification & Test Suite")
    print("=" * 70)
    start_time = time.time()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover agent tests
    agent_suite = loader.discover(
        start_dir=os.path.join(WORKSPACE_ROOT, "agent", "tests"),
        pattern="test_*.py",
    )
    suite.addTests(agent_suite)

    # Discover backend tests
    backend_suite = loader.discover(
        start_dir=os.path.join(WORKSPACE_ROOT, "backend", "tests"),
        pattern="test_*.py",
    )
    suite.addTests(backend_suite)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total_time = time.time() - start_time
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    print(f"Execution time: {total_time:.2f} seconds")
    print("=" * 70)

    if result.wasSuccessful():
        print("ALL FORMAL OPERATING SYSTEMS TEST CASES PASSED SUCCESSFULLY!")
        return 0
    else:
        print("TEST FAILURES DETECTED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

