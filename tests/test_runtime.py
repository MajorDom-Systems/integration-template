"""The integration run as the Hub runs it: started once its need is bound, restarted when it can't go on."""

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
