"""Tests that drive the controller through its lifecycle.

These are **prefilled to fail** against the unimplemented skeleton: every test below calls a
method that still raises `NotImplementedError`, so CI stays red until you implement the
controller.

Run these against a **virtual / simulated device** — a fake endpoint that speaks your
protocol in-process (no real hardware, no network), so CI is deterministic. Add a fixture
for it in `conftest.py` and have the controller talk to it. Each test should then assert on
**both sides**: what the controller reported back to the Hub (via `deps.output`) *and* what
actually landed on the device (the virtual device observed the command / changed state) —
don't just call the method and assume it worked. Keep a separate `real_iot_device`-marked
suite for hardware if you have a rig.

(The template's own CI excludes this file so the template repo stays green — see
`.github/workflows/test.yml`. Your integration repo runs it in full, and it's red until you
implement the controller.)
"""

from majordom_integration_sdk.schemas.command import DeviceCommand


async def test_pairs_a_discovered_device(controller, deps, discovery):
    await controller.pair_device(discovery, credentials=None)
    # TODO: verify pairing actually completed, both sides:
    #   - Hub side: `discovery.id`'s device is in `deps.output.connected_devices`.
    #   - Persistence: the device now exists via the injected repository
    #     (`async with deps.make_device_repository() as repo: await repo.state(<id>)`).
    #   - Device side: the virtual device registered the new session / accepted the credentials.


async def test_fetches_state(controller, deps, device):
    await controller.fetch(device)
    # TODO: verify the refresh reached the device and propagated back:
    #   - Set a known state on the virtual device first, then assert `deps.output.events`
    #     (or the repository's parameter states) now reflect exactly that state — not stale
    #     or default values.


async def test_sends_a_command(controller, device):
    parameter = device.parameters[0]
    command = DeviceCommand(device_id=device.id, parameter_id=parameter.id, value=False)
    await controller.send_command(command, device, parameter)
    # TODO: verify the command actually applied on the device, not just that the call
    #   returned: assert the virtual device received this exact write and its state changed
    #   to `value` (read it back). A no-op that silently succeeds must fail this test.


async def test_identifies(controller, device):
    await controller.identify(device)
    # TODO: assert the virtual device recorded an identify request (e.g. its identify counter
    #   incremented / the identify command was received).


async def test_unpairs(controller, device):
    await controller.unpair(device)
    # TODO: verify removal took effect both sides:
    #   - Persistence: the device is gone from the repository.
    #   - Device side: the virtual device saw the session torn down / was de-registered.
