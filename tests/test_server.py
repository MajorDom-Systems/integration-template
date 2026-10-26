"""The server the integration brings: connecting through its link, the settings and platform facts hooks,
and healing when the server goes away."""

import asyncio
from dataclasses import replace

import pytest
from majordom_integration_sdk import IntegrationError
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from tests.support import until
from tests.virtual_server import VirtualServer


async def test_connects_through_its_link_and_configures_the_server(
    controller: ExampleController, server: VirtualServer
):
    await controller.start()
    await server.received("name MajorDom")
    await controller.stop()


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


async def test_takes_a_new_server_name_while_the_server_is_away(
    controller: ExampleController,
    output: RecordingControllerOutput,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.01)
    await controller.start()
    await server.received("name MajorDom")
    await server.stop()  # e.g. its container restarts
    await until(lambda: "server-unreachable" in output.errors)

    before, controller.settings = controller.settings, ExampleController.Settings(server_name="Attic")
    assert await controller.settings_did_change(before)  # no restart: it hands the name over once reconnected
    await server.start()
    await server.received("name Attic")
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
    await controller.start()
    await server.received("name MajorDom")

    await server.stop()
    await asyncio.sleep(0.1)  # a few attempts fail while it's down
    server.lines.clear()
    await server.start()

    await server.received("name MajorDom")
    await until(lambda: not output.errors)  # resolved once connected again
    lost = IntegrationError("server-unreachable", "Lost the connection to the Example server, reconnecting.")
    assert output.error_log == [lost, "server-unreachable"]
    await controller.stop()


async def test_rides_out_a_quick_server_restart_without_telling_the_user(
    controller: ExampleController,
    output: RecordingControllerOutput,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.2)
    await controller.start()
    await server.received("name MajorDom")

    await server.stop()  # e.g. recreated with new settings, back before the first attempt
    server.lines.clear()
    await server.start()

    await server.received("name MajorDom")
    assert output.error_log == []
    await controller.stop()
