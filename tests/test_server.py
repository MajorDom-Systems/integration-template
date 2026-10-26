"""The server the integration brings: connecting through its link, the settings and platform facts hooks,
and healing when the server goes away."""

import asyncio
from dataclasses import replace

import pytest
from majordom_integration_sdk import IntegrationError
from majordom_integration_sdk.testing import RecordingControllerOutput
from pydantic import ValidationError

from integration_template import ExampleController
from tests.support import until
from tests.virtual_server import VirtualServer


async def test_connects_through_its_link_and_configures_the_server(
    controller: ExampleController, server: VirtualServer
):
    await controller.start()
    await server.received("name MajorDom")
    await controller.stop()


async def test_closes_its_connection_when_it_stops(controller: ExampleController, server: VirtualServer):
    await controller.start()
    await server.received("name MajorDom")
    assert server.is_connected
    await controller.stop()
    await until(lambda: not server.is_connected)


async def test_cant_start_without_the_server_and_starts_again_once_it_is_back(
    controller: ExampleController, server: VirtualServer
):
    await server.stop()
    with pytest.raises(OSError):
        await controller.start()  # the runtime tries again later, then gives up
    await controller.stop()  # the runtime stops it after a failed start, then starts the same object again

    await server.start()
    await controller.start()
    await server.received("name MajorDom")
    await controller.stop()


async def test_applies_a_new_server_name_in_place(controller: ExampleController, server: VirtualServer):
    await controller.start()
    before, controller.settings = controller.settings, ExampleController.Settings(server_name="Attic")
    assert await controller.settings_did_change(before)
    await server.received("name Attic")
    await controller.stop()


def test_refuses_a_server_name_that_would_break_the_protocol():
    with pytest.raises(ValidationError):
        ExampleController.Settings(server_name="Attic\nregion Mars")  # a second command


async def test_takes_a_new_server_name_while_the_server_is_away(
    controller: ExampleController,
    output: RecordingControllerOutput,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.01)
    monkeypatch.setattr(ExampleController, "_UNREACHABLE_AFTER", 0.05)
    await controller.start()
    await server.received("name MajorDom")
    await server.stop()  # e.g. its container restarts
    await until(lambda: "server-unreachable" in output.errors)

    before, controller.settings = controller.settings, ExampleController.Settings(server_name="Attic")
    assert await controller.settings_did_change(before)  # no restart: it hands the name over once reconnected
    await server.start()
    await server.received("name Attic")
    await controller.stop()


async def test_tells_the_hub_it_cant_go_on_when_it_cant_take_a_message(
    controller: ExampleController, output: RecordingControllerOutput, server: VirtualServer
):
    await controller.start()
    await server.received("name MajorDom")
    await server.send(b"x" * 70_000)  # longer than a line may be: a message it can't take
    await until(lambda: "crashed" in output.errors)
    assert not output.errors["crashed"].is_still_running  # the Hub restarts it
    await controller.stop()


async def test_asks_for_a_restart_only_for_a_new_region(controller: ExampleController):
    before, controller.platform = controller.platform, replace(controller.platform, thread_dataset="0e08000000")
    assert await controller.platform_facts_did_change(before)  # not its concern: it goes on
    before, controller.platform = controller.platform, replace(controller.platform, region="Europe")
    assert not await controller.platform_facts_did_change(before)


async def test_reconnects_when_the_server_comes_back(
    controller: ExampleController,
    output: RecordingControllerOutput,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.01)
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY_MAX", 0.04)
    monkeypatch.setattr(ExampleController, "_UNREACHABLE_AFTER", 0.05)
    await controller.start()
    await server.received("name MajorDom")

    await server.stop()
    await until(lambda: "server-unreachable" in output.errors)  # a few attempts failed while it's down
    server.lines.clear()
    await server.start()

    await server.received("name MajorDom")
    await until(lambda: not output.errors)  # resolved once connected again
    lost = IntegrationError("server-unreachable", "Lost the connection to the Example server, reconnecting.")
    assert output.error_log == [lost, "server-unreachable"]
    await controller.stop()


async def test_rides_out_a_server_restart_without_telling_the_user(
    controller: ExampleController,
    output: RecordingControllerOutput,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.01)
    await controller.start()
    await server.received("name MajorDom")

    await server.stop()  # e.g. recreated with new settings: back after a few seconds
    await asyncio.sleep(0.1)  # a few attempts fail meanwhile
    server.lines.clear()
    await server.start()

    await server.received("name MajorDom")
    assert output.error_log == []  # told only once it was away for about 15 s
    await controller.stop()
