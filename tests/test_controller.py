"""Tests that drive the controller through its lifecycle: the checklist for implementing it.

They are **prefilled to fail** against the unimplemented skeleton: each calls a method that still raises
`NotImplementedError`, so CI stays red until you implement the controller.

Run them against a **virtual / simulated device**: a fake endpoint that speaks your protocol in-process (no hardware,
no network), so tests are deterministic. Add a fixture for it in `conftest.py` and have the controller talk to it.
Each test then asserts on **both sides**: what the controller reported to the Hub (the recording `output`) *and* what
actually landed on the device. Replace each TODO with those assertions.

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
from majordom_integration_sdk.schemas.parameter import Parameter
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from integration_template.controller import ExampleDevice, ExampleDeviceState, ExampleParameter


def test_declares_its_types(controller: ExampleController):
    assert issubclass(controller.device_type, Device)
    assert issubclass(controller.device_state_type, DeviceState)
    assert issubclass(controller.parameter_type, Parameter)


async def test_opens_a_pairing_window(controller: ExampleController):
    # Delete this test together with `start_pairing_window` when your devices are always discoverable.
    await controller.start_pairing_window(60)
    # TODO: assert the virtual device can now be discovered (e.g. it joined, or the scan found it).


async def test_pairs_into_the_draft(
    controller: ExampleController,
    output: RecordingControllerOutput,
    store: dict[Any, dict[str, Any]],
    discovery: Discovery,
    draft: ExampleDeviceState,
):
    paired = await controller.pair_device(discovery, draft, credentials=None)

    # The draft comes back filled with what the controller learned; the user's fields and the Hub's id stay.
    assert paired.name == draft.name
    assert paired.id == draft.id
    assert paired.physical_id != discovery.id  # TODO: == controller.device_uuid(<the virtual device's serial>)
    assert paired.parameters
    assert paired.available
    # Nothing is saved or reported during pairing: the Hub does both after it writes the draft.
    assert store == {}
    assert output.connected_devices == []
    assert output.events == []
    # TODO: assert the virtual device is paired (holds the key or session kept in `paired.integration_data`).


async def test_pairing_refuses_an_id_another_record_holds(
    controller: ExampleController, store: dict[Any, dict[str, Any]], discovery: Discovery, draft: ExampleDeviceState
):
    # TODO: use the virtual device's serial or MAC, as your `pair_device` builds the physical id from it.
    store[uuid4()] = {"physical_id": str(controller.device_uuid("EX-1001")), "name": "Old device", "is_paired": False}
    with pytest.raises(DeviceIdTakenError):
        await controller.pair_device(discovery, draft, credentials=None)
    # TODO: assert nothing irreversible reached the virtual device.


async def test_failed_pairing_rolls_back_through_unpair(
    controller: ExampleController, store: dict[Any, dict[str, Any]], discovery: Discovery, draft: ExampleDeviceState
):
    # TODO: make the virtual device fail mid-pairing (after the first irreversible step), and expect its error.
    with pytest.raises(Exception):  # noqa: B017  TODO: your protocol's error
        await controller.pair_device(discovery, draft, credentials=None)
    assert store == {}
    # The Hub rolls back with the draft as `pair_device` left it.
    await controller.unpair(ExampleDevice.model_validate(draft.model_dump()))
    # TODO: assert the virtual device is back to unpaired, then let it succeed: a retry with a fresh draft pairs.
    paired = await controller.pair_device(
        discovery, draft.model_copy(update={"integration_data": None}), credentials=None
    )
    assert paired.parameters


async def test_pairing_is_idempotent(controller: ExampleController, discovery: Discovery, draft: ExampleDeviceState):
    # A retry that finds the device as the last attempt left it confirms it instead of refusing.
    first = await controller.pair_device(discovery, draft.model_copy(deep=True), credentials=None)
    again = await controller.pair_device(
        discovery, draft.model_copy(update={"integration_data": first.integration_data}), credentials=None
    )
    assert again.physical_id == first.physical_id
    # TODO: assert the virtual device holds one pairing, the one in `again.integration_data`.


async def test_unpairs(controller: ExampleController, device: ExampleDevice):
    await controller.unpair(device)
    # TODO: assert the virtual device forgot the pairing and its subscription, free for the next pairing.


async def test_unpair_tolerates_any_stage(
    controller: ExampleController, device: ExampleDevice, draft: ExampleDeviceState
):
    # A draft as it is before anything ran (no `integration_data`), and a second call: neither raises.
    await controller.unpair(ExampleDevice.model_validate(draft.model_dump()))
    await controller.unpair(device)
    await controller.unpair(device)


async def test_unpair_of_an_unreachable_device_raises(controller: ExampleController, device: ExampleDevice):
    # TODO: take the virtual device offline first.
    with pytest.raises(DeviceUnreachableError):
        await controller.unpair(device)


async def test_fetches_state(controller: ExampleController, output: RecordingControllerOutput, device: ExampleDevice):
    await controller.fetch(device)
    # TODO: set a known state on the virtual device first, then assert `output.events` carry exactly that state
    #   for `device.physical_id`, not stale or default values.


async def test_fetch_is_idempotent(controller: ExampleController, device: ExampleDevice):
    await controller.fetch(device)
    await controller.fetch(device)
    # TODO: assert the virtual device holds exactly one subscription.


async def test_fetch_of_an_unanswering_device_is_not_a_failure(
    controller: ExampleController, output: RecordingControllerOutput, device: ExampleDevice
):
    # TODO: take the virtual device offline first.
    await controller.fetch(device)
    assert output.events == []


async def test_sends_a_command(controller: ExampleController, device: ExampleDevice, parameter: ExampleParameter):
    command = DeviceCommand(device_id=device.id, parameter_id=parameter.id, value=False)
    await controller.send_command(command, device, parameter)
    # TODO: assert the virtual device received this exact write and its state changed to `value` (read it back).
    #   A no-op that silently succeeds must fail this test.


async def test_identifies(controller: ExampleController, device: ExampleDevice):
    await controller.identify(device)
    # TODO: assert the virtual device recorded an identify request.


async def test_forgets_its_discoveries_when_it_stops(controller: ExampleController, discovery: Discovery):
    await controller.start()
    controller._discoveries[discovery.id] = discovery  # as your discovery listener caches it
    await controller.stop()
    assert controller.discoveries == {}  # the device may be gone or paired elsewhere by the next start
