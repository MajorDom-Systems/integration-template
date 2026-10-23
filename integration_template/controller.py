"""A minimal MajorDom integration controller.

This is a worked skeleton — replace the TODO bodies with real protocol calls. It shows the
full lifecycle the Hub drives: discovery -> pairing -> commands -> teardown.

See the full guide at https://docs.majordom.io/device-integration.

A Controller bridges one external protocol/platform into the MajorDom language. The Hub
instantiates it with the app's services (`self.platform`) and its bound needs (`self.peripherals`)
and calls the methods below; the controller reports back to the Hub through `platform.output`
(a `ControllerOutput`).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Mapping
from typing import cast
from urllib.parse import urlsplit
from uuid import UUID

from majordom_integration_sdk import Context, Need
from majordom_integration_sdk.controller import AbstractController, Platform
from majordom_integration_sdk.peripherals import Bound
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, Discovery, Parameter, ProvidedCredentials
from pydantic import BaseModel

from integration_template.config import EXAMPLE_SERVER, ExampleSettings

logger = logging.getLogger(__name__)

# Output methods to call (see the docs):
# async def controller_did_receive_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_update_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_lose_discovery(self, controller: AbstractController, discovery_id: UUID): ...
# async def controller_did_connect_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_lose_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_receive_events(self, controller: AbstractController, events: Iterable[Event]): ...


class ExampleController(AbstractController[Device, Parameter]):
    """Bridges the Example protocol into MajorDom."""

    def __init__(self, platform: Platform, peripherals: Mapping[str, Bound] | None = None):
        super().__init__(platform, peripherals)
        self._discoveries: dict[UUID, Discovery] = {}
        # e.g. self._cancel_zeroconf: Callable[[], None] | None = None

    name = "Example"

    # What the controller connects to beyond the network, the server it brings along, and what the
    # user can set. The Hub runs EXAMPLE_SERVER, binds the need to it and hands over its URL in
    # `self.peripherals.endpoint("example")`; settings arrive validated in `self.platform.settings`.
    # Declare everything external as a Need: radios, Need("ble", ["router"]) (never raw Bluetooth),
    # Need("mdns", ["dns-sd"]), Need("upnp", ["ssdp"]) and the services you bring.
    # Leave them out if the protocol only uses the network.
    # See https://docs.majordom.io/device-integration/radios and .../settings.
    needs = [Need("example", ["echo"])]
    services = [EXAMPLE_SERVER]
    settings = ExampleSettings

    _RECONNECT_DELAY = 1.0  # seconds, doubled after every failed attempt
    _RECONNECT_DELAY_MAX = 30.0

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only — never scan here.
        return self._discoveries

    # Lifecycle -------------------------------------------------------------

    async def start(self) -> None:
        # Register with discovery (needed as peripherals), subscribe to protocol events, and reconcile the
        # state of already-paired devices here.
        # e.g. with Need("mdns", ["dns-sd"]) in `needs`:
        # self._cancel_zeroconf = self.peripherals.instance("mdns").register(self, {"_example._tcp.local."})
        await self._connect()  # raising here has the Hub retry start()
        self._keeper = asyncio.create_task(self._stay_connected())

    async def stop(self) -> None:
        # Cancel tasks and release every held resource.
        # e.g. if self._cancel_zeroconf: self._cancel_zeroconf()
        self._keeper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._keeper
        self._writer.close()

    # Hooks: return True when applied in place; the default (False) has the Hub restart the integration.

    async def settings_did_change(self, before: BaseModel | None) -> bool:
        before = cast(ExampleSettings, before or ExampleSettings())
        if self._settings.server_name != before.server_name:
            await self._sync_with_server()
            # The server applies its name only at start. The restart drops the connection, and
            # _stay_connected heals it, so the integration keeps running.
            await self.platform.services.restart(EXAMPLE_SERVER.name)
        return True

    async def context_did_change(self, before: Context) -> bool:
        return False  # the server gets the region when the controller connects: let the Hub restart it

    # Server ------------------------------------------------------------------

    @property
    def _settings(self) -> ExampleSettings:
        return cast(ExampleSettings, self.platform.settings or ExampleSettings())

    async def _connect(self) -> None:
        url = urlsplit(self.peripherals.endpoint("example").url)  # never build it yourself: the port may differ
        self._reader, self._writer = await asyncio.open_connection(url.hostname, url.port)
        await self._sync_with_server()

    async def _sync_with_server(self) -> None:
        """Hands the server its configuration; on every (re)connect."""
        self._writer.write(f"name {self._settings.server_name}\n".encode())
        if region := self.platform.context.region:
            self._writer.write(f"region {region}\n".encode())
        await self._writer.drain()

    async def _stay_connected(self) -> None:
        """Reconnects whenever the server goes away (e.g. it was restarted) until stop() cancels it,
        so the integration heals by itself instead of being restarted by the Hub."""
        while True:
            await self._listen()
            self._writer.close()
            message = "Lost the connection to the Example server, reconnecting."
            await self.platform.output.controller_did_encounter_error(self, message, still_running=True)
            delay = self._RECONNECT_DELAY
            while True:
                await asyncio.sleep(delay)
                try:
                    await self._connect()
                    break
                except OSError as error:
                    logger.info(f"[{self.name}] the server is not back yet: {error!r}")
                    delay = min(delay * 2, self._RECONNECT_DELAY_MAX)

    async def _listen(self) -> None:
        """Reads the server's messages until it closes the connection."""
        with contextlib.suppress(OSError):
            while line := await self._reader.readline():
                # Turn protocol messages into events here: controller_did_receive_events(...)
                logger.debug(f"[{self.name}] server: {line!r}")

    # Hub -> device ---------------------------------------------------------

    async def pair_device(self, discovery: Discovery, credentials: ProvidedCredentials | None) -> None:
        # Establish a session with the device, then report success to the Hub:
        # await self.platform.output.controller_did_connect_device(self, self.device_uuid(...))
        raise NotImplementedError

    async def unpair(self, device: Device) -> None:
        raise NotImplementedError

    async def identify(self, device: Device) -> None:
        # Ask the device to blink/beep so the user can locate it.
        raise NotImplementedError

    async def fetch(self, device: Device) -> None:
        # Refresh the device and its parameters, reporting changes via
        # self.platform.output.controller_did_receive_events(self, [...]).
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand, device: Device, parameter: Parameter) -> None:
        # Translate the MajorDom command into a protocol-level write.
        raise NotImplementedError
