"""Shared pytest fixtures for the whole suite live here.

conftest.py is auto-discovered by pytest — no import needed.

The `controller` fixture below wires the integration's Controller with the SDK's test
doubles (a recording `ControllerOutput`, an in-memory device repository, and fake discovery
services), so tests can drive it exactly as the Hub would — without a running Hub.
"""

import pytest
from majordom_sdk.testing import build_test_dependencies

from integration_template import ExampleController


@pytest.fixture
def deps():
    """SDK-provided test dependencies (recording output + in-memory repo + fake discovery)."""
    return build_test_dependencies()


@pytest.fixture
def controller(deps) -> ExampleController:
    return ExampleController(deps)
