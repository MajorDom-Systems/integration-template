"""Tests that drive the controller through its lifecycle.

These are **prefilled to fail** against the unimplemented skeleton: every test below calls a
method that still raises `NotImplementedError`, so CI stays red until you implement the
controller. Replace each body with real assertions about what your integration reports back
to the Hub via the recording output in `deps.output` (e.g. `deps.output.connected_devices`,
`deps.output.events`). Add a `real_iot_device`-marked suite too if you validate on hardware.

(The template's own CI excludes this file so the template repo stays green — see
`.github/workflows/test.yml`. Your integration repo runs it in full, and it's red until you
implement the controller.)
"""

from majordom_integration_sdk.schemas.command import DeviceCommand


async def test_pairs_a_discovered_device(controller, deps, discovery):
    await controller.pair_device(discovery, credentials=None)
    # e.g. assert deps.output.connected_devices, and the device is now in the repository.


async def test_fetches_state(controller, deps, device):
    await controller.fetch(device)
    # e.g. assert deps.output.events reflects the refreshed parameter values.


async def test_sends_a_command(controller, device):
    parameter = device.parameters[0]
    command = DeviceCommand(device_id=device.id, parameter_id=parameter.id, value=False)
    await controller.send_command(command, device, parameter)


async def test_identifies(controller, device):
    await controller.identify(device)


async def test_unpairs(controller, device):
    await controller.unpair(device)
