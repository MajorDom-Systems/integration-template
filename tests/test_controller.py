"""Example tests for the integration controller.

These drive the controller through its lifecycle and assert on what it reports back to the
Hub via the recording `ControllerOutput` in `deps.output`. Flesh these out per protocol;
add a `real_iot_device`-marked suite for hardware validation if you have a rig.
"""

import pytest


async def test_starts_and_stops(controller):
    await controller.start()
    await controller.stop()


async def test_name_and_slug(controller):
    assert controller.name == "Example"
    assert controller.name_slug == "example"


@pytest.mark.skip(reason="template placeholder — implement against the Example protocol")
async def test_pairs_a_discovered_device(controller, deps):
    # discovery = next(iter(controller.discoveries.values()))
    # await controller.pair_device(discovery, credentials=None)
    # assert deps.output.connected_devices  # RecordingControllerOutput captured the callback
    ...
