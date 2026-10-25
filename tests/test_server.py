"""The server the integration brings: connecting through its link, the settings and context hooks,
and healing when the server goes away."""

import asyncio
from typing import cast

import pytest
from majordom_integration_sdk import Context, IntegrationError
from majordom_integration_sdk.controller import Platform
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from tests.conftest import VirtualServer


async def test_connects_through_its_link_and_configures_the_server(
    controller: ExampleController, server: VirtualServer
):
    await controller.start()
    await server.received("name MajorDom")
    await controller.stop()


async def test_applies_a_new_server_name_in_place(controller: ExampleController, server: VirtualServer):
    await controller.start()
    before, controller.settings = controller.settings, ExampleController.Settings(server_name="Attic")
    assert await controller.settings_did_change(before)
    await server.received("name Attic")
    await controller.stop()


async def test_asks_for_a_restart_when_the_context_changes(controller: ExampleController):
    assert not await controller.context_did_change(Context(region="Europe"))


async def test_reconnects_when_the_server_comes_back(
    controller: ExampleController,
    deps: Platform,
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
    output = cast(RecordingControllerOutput, deps.output)
    async with asyncio.timeout(1):
        while output.errors:  # resolved once connected again
            await asyncio.sleep(0.01)
    lost = IntegrationError("server-unreachable", "Lost the connection to the Example server, reconnecting.")
    assert output.error_log == [lost, "server-unreachable"]
    await controller.stop()
