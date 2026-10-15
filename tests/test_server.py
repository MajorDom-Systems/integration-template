"""The server the integration brings: connecting through its link, the settings and context hooks,
and healing when the server goes away."""

import asyncio
from typing import cast

import pytest
from majordom_integration_sdk import Context
from majordom_integration_sdk.controller import AbstractController
from majordom_integration_sdk.testing import RecordingControllerOutput

from integration_template import ExampleController
from integration_template.config import ExampleSettings
from tests.conftest import FakeServiceControl, VirtualServer


async def test_connects_through_its_link_and_configures_the_server(
    controller: ExampleController, server: VirtualServer
) -> None:
    await controller.start()
    await server.received("name MajorDom")
    await controller.stop()


async def test_applies_a_new_server_name_in_place(
    controller: ExampleController,
    deps: AbstractController.Dependencies,
    server: VirtualServer,
    services: FakeServiceControl,
) -> None:
    await controller.start()
    controller.dependencies = deps.copy(settings=ExampleSettings(server_name="Attic"))
    assert await controller.settings_did_change(deps.settings)
    await server.received("name Attic")
    assert services.restarted == ["example-server"]
    await controller.stop()


async def test_asks_for_a_restart_when_the_context_changes(controller: ExampleController) -> None:
    assert not await controller.context_did_change(Context(region="Europe"))


async def test_reconnects_when_the_server_comes_back(
    controller: ExampleController,
    deps: AbstractController.Dependencies,
    server: VirtualServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY", 0.01)
    monkeypatch.setattr(ExampleController, "_RECONNECT_DELAY_MAX", 0.04)
    await controller.start()
    await server.received("name MajorDom")

    await server.stop()
    await asyncio.sleep(0.1)  # a few attempts fail while it's down
    server.lines.clear()
    await server.start()

    await server.received("name MajorDom")
    errors = cast(RecordingControllerOutput, deps.output).errors
    assert errors == [("Lost the connection to the Example server, reconnecting.", True)]
    await controller.stop()
