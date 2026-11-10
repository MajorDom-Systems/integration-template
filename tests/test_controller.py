"""Tests that drive the controller through its lifecycle.

These are **prefilled to fail** against the unimplemented skeleton: every test below calls a
method that still raises `NotImplementedError`, so CI stays red until you implement the
controller.

Run these against a **virtual / simulated device** — a fake endpoint that speaks your
protocol in-process (no real hardware, no network), so CI is deterministic. Add a fixture
for it in `conftest.py` and have the controller talk to it. Each test should then assert on
**both sides**: what the controller reported back to the Hub (the recording `output`) *and* what
actually landed on the device (the virtual device observed the command / changed state) —
don't just call the method and assume it worked.

Persistence is the Hub's job (see `conftest.py`): `pair_device` fills and returns a draft, the
Hub saves it. Assert on the returned draft and the controller's protocol behaviour — never that
the integration created a device row.

(The template's own CI excludes this file so the template repo stays green — see
`.github/workflows/test.yml`. Your integration repo runs it in full, and it's red until you
implement the controller.)
"""

from typing import Any

import pytest
from majordom_integration_sdk import DeviceIdTakenError
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery
from majordom_integration_sdk.schemas.parameter import ParameterState
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController


async def test_pairs_into_the_draft(
    controller: ExampleController,
    output: RecordingControllerOutput,
    store: dict[Any, dict[str, Any]],
    discovery: Discovery,
    draft: DeviceState,
):
    paired = await controller.pair_device(discovery, draft, credentials=None)

    # The draft comes back filled with what the controller learned; the user's fields stay.
    assert paired.name == draft.name
    assert paired.integration_data is not None
    assert paired.parameters
    # Nothing is saved or reported during pairing: the Hub does both after it writes the draft.
    assert store == {}
    assert output.connected_devices == []
    assert output.events == []
    # TODO: Device side: the virtual device accepted the credentials / opened a session.


async def test_pairing_refuses_an_id_another_record_holds(
    controller: ExampleController,
    store: dict[Any, dict[str, Any]],
    discovery: Discovery,
    draft: DeviceState,
):
    # TODO: seed `store` with a record whose id is the one your pair_device derives for the virtual device
    #   (`controller.device_uuid(<its serial>)`), e.g. {"name": "Old lamp", "is_paired": False}.
    with pytest.raises(DeviceIdTakenError):
        await controller.pair_device(discovery, draft, credentials=None)
    # TODO: Device side: nothing irreversible ran, the virtual device is untouched, and the draft still says so.


async def test_unpair_rolls_back_a_half_paired_draft(controller: ExampleController, draft: DeviceState):
    # The Hub calls `unpair(draft)` when pairing fails at any stage: here the draft is as it was before anything
    # ran, with no `integration_data`. It must not raise or wait.
    await controller.unpair(Device.model_validate(draft.model_dump()))
    # TODO: Device side: nothing is left behind (no key set, no node included), and a second call changes nothing.


async def test_fetches_state(controller: ExampleController, output: RecordingControllerOutput, device: Device):
    await controller.fetch(device)
    # TODO: verify the refresh reached the device and propagated back:
    #   - Set a known state on the virtual device first, then assert `output.events`
    #     now reflect exactly that state — not stale or default values.


async def test_fetch_is_idempotent(controller: ExampleController, device: Device):
    await controller.fetch(device)
    await controller.fetch(device)
    # TODO: Device side: the virtual device holds exactly one event subscription, not two.


async def test_sends_a_command(controller: ExampleController, device: Device, parameter: ParameterState):
    command = DeviceCommand(device_id=device.id, parameter_id=parameter.id, value=False)
    await controller.send_command(command, device, parameter)
    # TODO: verify the command actually applied on the device, not just that the call
    #   returned: assert the virtual device received this exact write and its state changed
    #   to `value` (read it back). A no-op that silently succeeds must fail this test.


async def test_identifies(controller: ExampleController, device: Device):
    await controller.identify(device)
    # TODO: assert the virtual device recorded an identify request (e.g. its identify counter
    #   incremented / the identify command was received).


async def test_unpairs(controller: ExampleController, device: Device):
    await controller.unpair(device)
    # TODO: verify removal took effect:
    #   - Device side: the virtual device saw the session torn down / was de-registered.
    #   - Controller: the device is gone — no more connections or commands should be accepted.
