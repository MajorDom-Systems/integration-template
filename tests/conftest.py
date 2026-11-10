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

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
from majordom_integration_sdk import Platform
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery
from majordom_integration_sdk.schemas.parameter import (
    ParameterDataType,
    ParameterRole,
    ParameterState,
    ParameterVisibility,
)
from majordom_integration_sdk.testing import RecordingControllerOutput, build_test_platform

from integration_template import ExampleController
from integration_template.acme import AcmeClient, AcmeLamp

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
def virtual_lamp() -> AcmeLamp:
    """The virtual device: a fake lamp on the other end of `acme.py`, to set up and to check what reached it. Swap it
    for a fake of your own protocol's device."""
    return AcmeLamp(serial="AC-1001", address="10.0.0.7")


@pytest.fixture
def controller(platform: Platform, output: RecordingControllerOutput, virtual_lamp: AcmeLamp) -> ExampleController:
    controller = ExampleController(platform)
    controller.output = output
    controller.acme = AcmeClient([virtual_lamp])
    return controller


async def _seed(platform: Platform, device: DeviceState):
    """Persist a device the way the Hub would, before handing control to the integration."""
    async with platform.make_device_repository(INTEGRATION) as repo:
        await repo.save(device)


@pytest.fixture
async def discovery(controller: ExampleController) -> AsyncIterator[Discovery]:
    """A discovered-but-unpaired device, as the started controller surfaced it."""
    await controller.start()
    yield next(iter(controller.discoveries.values()))
    await controller.stop()


@pytest.fixture
def draft(discovery: Discovery) -> DeviceState:
    """The draft the Hub hands to `pair_device`: built from the user's input (name, room), the id of the discovery
    and no parameters yet. Nothing is stored: the Hub saves what `pair_device` returns."""
    return DeviceState(
        id=discovery.id,
        name="Living Room Lamp",
        room_id=uuid4(),
        transport=discovery.transport,
        integration=INTEGRATION,
        manufacturer=discovery.device_manufacturer,
        parameters=[],
    )


@pytest.fixture
async def device_state(platform: Platform, controller: ExampleController, virtual_lamp: AcmeLamp) -> DeviceState:
    """An already-paired device with one on/off parameter, as the Hub *stores* it (the full state, with parameters),
    and the virtual lamp holding the key it was paired with. Seeded into the repository."""
    virtual_lamp.key = "secret"
    device_id = uuid4()
    power = ParameterState(
        id=controller.parameter_uuid(device_id, "power"),
        name="Power",
        data_type=ParameterDataType.bool,
        role=ParameterRole.control,
        visibility=ParameterVisibility.user,
        integration_data=None,
        value=True,
    )
    state = DeviceState(
        id=device_id,
        name="Living Room Lamp",
        room_id=uuid4(),
        transport="wifi",
        integration=INTEGRATION,
        manufacturer="ACME",
        integration_data={"serial": virtual_lamp.serial, "address": virtual_lamp.address, "key": "secret"},
        parameters=[power],
    )
    await _seed(platform, state)
    return state


@pytest.fixture
def device(device_state: DeviceState) -> Device:
    """The device as the Hub *passes* it to `fetch`/`identify`/`unpair`/`send_command` — a
    `Device` (info + integration_data), without the parameter list."""
    return Device.model_validate(device_state.model_dump())


@pytest.fixture
def parameter(device_state: DeviceState) -> ParameterState:
    """The target parameter for `send_command`, paired with `device`."""
    return device_state.parameters[0]
