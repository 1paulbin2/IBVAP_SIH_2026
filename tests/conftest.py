"""Shared test configuration and fixtures."""

import pytest


# Tell pytest-asyncio to use auto mode so @pytest.mark.asyncio is not
# strictly required on every async test, but we still apply it explicitly
# for clarity.
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark a test as async")
