"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_standard_tap_tests

from tap_decentraland_api.tap import TapDecentralandAPI

SAMPLE_CONFIG = {
    "api_url": "https://api.decentraland.net"
}


# Run standard built-in tap tests from the SDK:
def test_standard_tap_tests():
    """Run standard tap tests from the SDK."""
    tests = get_standard_tap_tests(
        TapDecentralandAPI,
        config=SAMPLE_CONFIG
    )
    for test in tests:
        test()


