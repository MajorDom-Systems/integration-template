"""The integration run as the Hub runs it: started once its need is bound, restarted for a new region and when it
can't go on."""

from dataclasses import replace

from majordom_integration_sdk.runtime import PeripheralState, Runtime, StatusKind
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from tests.support import until
from tests.virtual_server import VirtualServer


async def test_is_restarted_when_it_cant_go_on(
    runtime: Runtime, controller: ExampleController, output: RecordingControllerOutput, server: VirtualServer
):
    await server.received("name MajorDom")
    await server.send(b"x" * 70_000)
    await until(lambda: runtime.status(controller).kind == StatusKind.RETRYING)
    status = runtime.status(controller)
    assert status.state == PeripheralState.WAITING  # started again after a delay, then failed if it keeps crashing
    assert status.detail.startswith(output.errors["crashed"].message)


async def test_is_restarted_for_a_new_region_only(runtime: Runtime, server: VirtualServer):
    await server.received("name MajorDom")
    await runtime.update_platform(replace(runtime.platform, thread_dataset="0e08000000"))  # not its concern
    await runtime.update_platform(replace(runtime.platform, region="Europe"))
    await server.received("region Europe")  # told when it connects again
    assert server.lines.count("name MajorDom") == 2
