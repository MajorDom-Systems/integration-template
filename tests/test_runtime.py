"""The integration run as the Hub runs it: started once its need is bound, restarted for a new region and when it
can't go on, its server recreated with new settings."""

import json
from dataclasses import replace
from pathlib import Path

from majordom_integration_sdk import Need, Peripherals
from majordom_integration_sdk.runtime import PeripheralState, Pinned, Runtime, StatusKind
from majordom_integration_sdk.testing import (
    FakeCompose,
    FakePeripheral,
    RecordingControllerOutput,
    RecordingRuntimeOutput,
    build_test_platform,
)

from integration_template import ExampleController
from integration_template.config import example_server
from tests.support import until
from tests.virtual_server import VirtualServer


async def test_is_restarted_when_it_cant_go_on(
    tmp_path: Path,
    controller: ExampleController,
    bound: Peripherals,
    output: RecordingControllerOutput,
    server: VirtualServer,
):
    statuses = RecordingRuntimeOutput()
    runtime = Runtime(
        tmp_path,
        [Pinned(bound.endpoint("example")), controller],
        platform=controller.platform,
        controller_output=output,
        output=statuses,
        retry_delays=(0.01, 0.01, 0.01),  # the Hub waits 5, 30, 120 s
    )
    await runtime.start()
    await server.received("name MajorDom")
    await server.send(b"x" * 70_000)
    await until(lambda: server.lines.count("name MajorDom") == 2)  # started again: it connected anew
    await until(lambda: runtime.status(controller).state == PeripheralState.RUNNING)
    waited = [s for key, s in statuses.statuses if key == controller.key and s.kind == StatusKind.RETRYING]
    assert waited and waited[0].state == PeripheralState.WAITING  # after a delay, then failed if it keeps crashing
    assert waited[0].detail.startswith(output.errors["crashed"].message)
    await runtime.stop()


async def test_is_restarted_for_a_new_region_only(runtime: Runtime, server: VirtualServer):
    await server.received("name MajorDom")
    await runtime.update_platform(replace(runtime.platform, thread_dataset="0e08000000"))  # not its concern
    await runtime.update_platform(replace(runtime.platform, region="Europe"))
    await server.received("region Europe")  # told when it connects again
    assert server.lines.count("name MajorDom") == 2


async def test_recreates_the_server_with_new_settings(tmp_path: Path):
    compose, server = FakeCompose(), example_server()
    controller = FakePeripheral("controller", [Need("example", ["echo"])])
    runtime = Runtime(tmp_path, [compose, server, controller], platform=build_test_platform(tmp_path / "documents"))

    def greeting() -> str:
        rendered = json.loads((compose.platform.documents_folder(compose) / "compose.json").read_text())
        return rendered["services"]["example-server"]["command"][-1]

    await runtime.start()
    await until(lambda: runtime.status(server).state == PeripheralState.RUNNING)
    assert greeting() == "hello"
    await runtime.update_settings(server, {"greeting": "hi"})
    await until(lambda: greeting() == "hi")
    assert controller.calls == ["start"]  # not restarted with it: the controller reconnects
    await runtime.stop()
