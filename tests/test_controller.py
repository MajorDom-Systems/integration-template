"""Tests that drive the controller through its lifecycle: the checklist for implementing it.

They are **prefilled to fail** against the unimplemented template: each calls a method that still raises
`NotImplementedError`, so CI stays red until you implement the controller. Once a method's commented-out body is
uncommented as it is, its tests pass against the fake library in `acme.py`.

The virtual device is `virtual_lamp` (see `conftest.py`): a fake endpoint that speaks your protocol in-process, so
tests are deterministic. Each test asserts on **both sides**: what the controller reported to the Hub (the recording
`output`) *and* what actually landed on the device. Swap the lamp for a fake of your own device and keep the shape.

Persistence is the Hub's job (see `conftest.py`): `pair_device` fills and returns a draft, the Hub saves it. Assert on
the returned draft and the protocol behaviour, never that the integration created a device row.

(The template's own CI excludes this file so the template repo stays green, see `.github/workflows/test.yml`. Your
integration repo runs it in full, and it is red until you implement the controller.)
"""

from typing import Any
from uuid import uuid4

import pytest
from majordom_integration_sdk import DeviceIdTakenError, DeviceUnreachableError
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery
from majordom_integration_sdk.schemas.event import DeviceParameterChange
from majordom_integration_sdk.schemas.parameter import Parameter, ParameterState
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from integration_template.acme import AcmeError, AcmeLamp


def test_declares_its_types(controller: ExampleController):
    # Passes when the overrides are uncommented as they are, or deleted: the defaults are these.
    assert issubclass(controller.device_type, Device)
    assert issubclass(controller.device_state_type, DeviceState)
    assert issubclass(controller.parameter_type, Parameter)


async def test_starts_and_stops(controller: ExampleController, output: RecordingControllerOutput):
    await controller.start()
    assert controller.acme.is_open
    assert len(controller.discoveries) == 1
    assert len(output.received_discoveries) == 1

    await controller.stop()
    assert not controller.acme.is_open
    assert controller.discoveries == {}


async def test_opens_a_pairing_window(controller: ExampleController):
    # Delete this test together with `start_pairing_window` when your devices are always discoverable.
    await controller.start_pairing_window(60)
    assert controller.acme.pairing_open


async def test_pairs_into_the_draft(
    controller: ExampleController,
    output: RecordingControllerOutput,
    store: dict[Any, dict[str, Any]],
    virtual_lamp: AcmeLamp,
    discovery: Discovery,
    draft: DeviceState,
):
    paired = await controller.pair_device(discovery, draft, credentials=None)

    # The draft comes back filled with what the controller learned; the user's fields stay.
    assert paired.name == draft.name
    assert paired.id == draft.id  # the Hub's, never changed
    assert paired.physical_id == controller.device_uuid(virtual_lamp.serial)
    assert paired.integration_data["key"] == virtual_lamp.key is not None
    assert paired.parameters
    assert paired.available
    # Nothing is saved or reported during pairing: the Hub does both after it writes the draft.
    assert store == {}
    assert output.connected_devices == []
    assert output.events == []


async def test_pairing_refuses_an_id_another_record_holds(
    controller: ExampleController,
    store: dict[Any, dict[str, Any]],
    virtual_lamp: AcmeLamp,
    discovery: Discovery,
    draft: DeviceState,
):
    store[uuid4()] = {
        "physical_id": str(controller.device_uuid(virtual_lamp.serial)),
        "name": "Old lamp",
        "is_paired": False,
    }
    with pytest.raises(DeviceIdTakenError):
        await controller.pair_device(discovery, draft, credentials=None)
    # Nothing irreversible ran.
    assert virtual_lamp.key is None


async def test_failed_pairing_rolls_back_through_unpair(
    controller: ExampleController,
    output: RecordingControllerOutput,
    store: dict[Any, dict[str, Any]],
    virtual_lamp: AcmeLamp,
    discovery: Discovery,
    draft: DeviceState,
):
    virtual_lamp.read_fails = True
    with pytest.raises(AcmeError):
        await controller.pair_device(discovery, draft, credentials=None)
    # Nothing was saved or reported; the draft holds what ran, so the Hub's `unpair(draft)` undoes it.
    assert store == {}
    assert output.connected_devices == []
    await controller.unpair(Device.model_validate(draft.model_dump()))
    assert virtual_lamp.key is None

    virtual_lamp.read_fails = False
    paired = await controller.pair_device(
        discovery, draft.model_copy(update={"integration_data": None}), credentials=None
    )
    assert paired.parameters


async def test_pairing_is_idempotent(
    controller: ExampleController, virtual_lamp: AcmeLamp, discovery: Discovery, draft: DeviceState
):
    # Pairing again onto what the last attempt left (the lamp keyed, its key in the draft): confirmed, not refused.
    first = await controller.pair_device(discovery, draft.model_copy(deep=True), credentials=None)
    again = await controller.pair_device(
        discovery, draft.model_copy(update={"integration_data": first.integration_data}), credentials=None
    )
    assert again.physical_id == first.physical_id
    assert virtual_lamp.key == first.integration_data["key"]


async def test_unpairs(controller: ExampleController, virtual_lamp: AcmeLamp, device: Device):
    await controller.fetch(device)
    assert virtual_lamp.subscriptions

    await controller.unpair(device)
    # The lamp is free for the next pairing.
    assert virtual_lamp.key is None
    assert virtual_lamp.subscriptions == []


async def test_unpair_tolerates_any_stage(
    controller: ExampleController, virtual_lamp: AcmeLamp, device: Device, draft: DeviceState
):
    # A draft as it is before anything ran (no `integration_data`), and a second call: neither raises.
    await controller.unpair(Device.model_validate(draft.model_dump()))
    await controller.unpair(device)
    await controller.unpair(device)
    assert virtual_lamp.key is None


async def test_unpair_of_an_unreachable_device_raises(
    controller: ExampleController, virtual_lamp: AcmeLamp, device: Device
):
    virtual_lamp.online = False
    with pytest.raises(DeviceUnreachableError):
        await controller.unpair(device)


async def test_fetches_state(
    controller: ExampleController, output: RecordingControllerOutput, virtual_lamp: AcmeLamp, device: Device
):
    virtual_lamp.power = False
    await controller.fetch(device)
    assert [
        (event.value, event.physical_id) for event in output.events if isinstance(event, DeviceParameterChange)
    ] == [(False, device.physical_id)]


async def test_fetch_is_idempotent(controller: ExampleController, virtual_lamp: AcmeLamp, device: Device):
    await controller.fetch(device)
    await controller.fetch(device)
    assert virtual_lamp.subscriptions == [str(device.physical_id)]


async def test_fetch_of_an_unanswering_device_is_not_a_failure(
    controller: ExampleController, output: RecordingControllerOutput, virtual_lamp: AcmeLamp, device: Device
):
    virtual_lamp.online = False
    await controller.fetch(device)
    assert output.events == []


async def test_sends_a_command(
    controller: ExampleController, virtual_lamp: AcmeLamp, device: Device, parameter: ParameterState
):
    command = DeviceCommand(device_id=device.id, parameter_id=parameter.id, value=False)
    await controller.send_command(command, device, parameter)
    # The lamp changed, not just the call returned: a no-op that silently succeeds fails here.
    assert virtual_lamp.power is False


async def test_identifies(controller: ExampleController, virtual_lamp: AcmeLamp, device: Device):
    await controller.identify(device)
    assert virtual_lamp.blinks == 1
