"""Shared pytest fixtures for the whole suite live here.

conftest.py is auto-discovered by pytest — no import needed.

The fixtures below wire the integration's Controller with the SDK's test doubles (a
recording `ControllerOutput`, an in-memory device repository, and fake discovery services)
and build a sample `Discovery`/`DeviceState`, so tests can drive the controller exactly as
the Hub would — without a running Hub.
"""

from uuid import uuid4

import pytest
from majordom_integration_sdk.schemas.device import CredentialsType, DeviceState, Discovery
from majordom_integration_sdk.schemas.parameter import (
    ParameterDataType,
    ParameterRole,
    ParameterState,
    ParameterVisibility,
)
from majordom_integration_sdk.testing import build_test_dependencies

from integration_template import ExampleController

INTEGRATION = "example"


@pytest.fixture
def deps():
    """SDK-provided test dependencies (recording output + in-memory repo + fake discovery)."""
    return build_test_dependencies(integration=INTEGRATION)


@pytest.fixture
def controller(deps) -> ExampleController:
    return ExampleController(deps)


@pytest.fixture
def discovery() -> Discovery:
    """A sample discovered-but-unpaired device."""
    return Discovery(
        id=uuid4(),
        integration=INTEGRATION,
        expected_credentials_options=[CredentialsType.none],
        transport="wifi",
        device_manufacturer="ACME",
        device_name="Example Lamp",
        device_category=None,
        device_icon=None,
    )


@pytest.fixture
def device() -> DeviceState:
    """A sample paired device with a single on/off parameter."""
    power = ParameterState(
        id=uuid4(),
        name="Power",
        data_type=ParameterDataType.bool,
        role=ParameterRole.control,
        visibility=ParameterVisibility.user,
        integration_data=None,
    ).with_value(True)
    return DeviceState(
        id=uuid4(),
        name="Example Lamp",
        room_id=uuid4(),
        transport="wifi",
        integration=INTEGRATION,
        manufacturer="ACME",
        parameters=[power],
    )
