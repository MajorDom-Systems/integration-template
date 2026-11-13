"""Shared pytest fixtures for the whole suite live here.

conftest.py is auto-discovered by pytest — no import needed.

The fixtures wire the integration's Controller with the SDK's test doubles (a test `Platform` with an in-memory
device repository, and a recording `ControllerOutput`) and build sample `Discovery`/`DeviceState` objects, so tests
can drive the controller exactly as the Hub would — without a running Hub.

**Device persistence is the Hub's core business logic, not the integration's.** The Hub builds the draft a pairing
fills, saves what `pair_device` returns, and only then reports the device connected. These fixtures therefore seed
the repository only for devices that are already paired, the way the Hub stored them; the tests never make the
integration persist a device itself.
"""

from typing import Any
from uuid import uuid4

import pytest
from majordom_integration_sdk import Platform
from majordom_integration_sdk.schemas.device import CredentialsType, DeviceState, Discovery
from majordom_integration_sdk.schemas.parameter import (
    ParameterDataType,
    ParameterRole,
    ParameterState,
    ParameterVisibility,
)
from majordom_integration_sdk.testing import RecordingControllerOutput, build_test_platform

from integration_template import ExampleController
from integration_template.controller import ExampleDevice, ExampleDeviceState, ExampleParameter

INTEGRATION = "example"


@pytest.fixture
def store() -> dict[Any, dict[str, Any]]:
    """Every device record the Hub keeps, by id. Seed it to give `check_device_id` a record to collide with."""
    return {}


@pytest.fixture
def platform(store: dict[Any, dict[str, Any]]) -> Platform:
    """SDK-provided test platform: in-memory device repository over `store`, and a working `check_device_id`."""
    return build_test_platform(store=store)


@pytest.fixture
def output() -> RecordingControllerOutput:
    return RecordingControllerOutput()


@pytest.fixture
def controller(platform: Platform, output: RecordingControllerOutput) -> ExampleController:
    controller = ExampleController(platform)
    controller.output = output
    return controller


# A virtual / simulated device: a fake endpoint that speaks your protocol in-process (no hardware, no network), so
# tests are deterministic and can assert what actually reached the device. Stand one up here and have the controller
# talk to it (e.g. a mock transport injected into the controller). Tests then assert on both the controller's reports
# (`output`) and this object's observed state.
#
# @pytest.fixture
# def virtual_device():
#     device = VirtualExampleDevice()  # your in-process fake
#     device.start()
#     yield device
#     device.stop()


async def _seed(platform: Platform, device: DeviceState):
    """Persist a device the way the Hub would, before handing control to the integration."""
    async with platform.make_device_repository(INTEGRATION) as repo:
        await repo.save(device)


@pytest.fixture
def discovery() -> Discovery:
    """A discovered-but-unpaired device, as the started controller would surface it."""
    return Discovery(
        id=uuid4(),
        integration=INTEGRATION,
        expected_credentials_options=[CredentialsType.none],
        transport="wifi",
        device_manufacturer="Example",
        device_name="Example device",
        device_category=None,
        device_icon=None,
    )


@pytest.fixture
def draft(discovery: Discovery) -> ExampleDeviceState:
    """The draft the Hub hands to `pair_device`: built from the user's input (name, room), the Hub's own `id`, the
    discovery's id as a placeholder `physical_id` and no parameters yet. Nothing is stored: the Hub saves what
    `pair_device` returns."""
    return ExampleDeviceState(
        id=uuid4(),
        physical_id=discovery.id,
        name="Living Room Device",
        room_id=uuid4(),
        transport=discovery.transport,
        integration=INTEGRATION,
        manufacturer=discovery.device_manufacturer,
        parameters=[],
    )


@pytest.fixture
async def device_state(platform: Platform, controller: ExampleController) -> ExampleDeviceState:
    """An already-paired device with one on/off parameter, as the Hub *stores* it (the full state, with parameters).
    Seeded into the repository. TODO: pair your virtual device to match it."""
    physical_id = controller.device_uuid("EX-1001")  # the virtual device's serial or MAC
    power = ParameterState(
        id=controller.parameter_uuid(physical_id, "power"),
        name="Power",
        data_type=ParameterDataType.bool,
        role=ParameterRole.control,
        visibility=ParameterVisibility.user,
        integration_data={},  # TODO: what your `pair_device` keeps for this parameter
        value=True,
    )
    state = ExampleDeviceState(
        id=uuid4(),
        physical_id=physical_id,
        name="Living Room Device",
        room_id=uuid4(),
        transport="wifi",
        integration=INTEGRATION,
        manufacturer="Example",
        integration_data={},  # TODO: what your `pair_device` keeps for the virtual device
        parameters=[power],
    )
    await _seed(platform, state)
    return state


@pytest.fixture
def device(device_state: ExampleDeviceState) -> ExampleDevice:
    """The device as the Hub *passes* it to `fetch`/`identify`/`unpair`/`send_command` — an
    `ExampleDevice` (info + integration_data), without the parameter list."""
    return ExampleDevice.model_validate(device_state.model_dump())


@pytest.fixture
def parameter(device_state: ExampleDeviceState) -> ExampleParameter:
    """The target parameter for `send_command`, paired with `device`."""
    return ExampleParameter.model_validate(device_state.parameters[0].model_dump())
