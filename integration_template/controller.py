"""A minimal MajorDom integration controller.

This is a worked skeleton — replace the bodies raising NotImplementedError with real protocol calls.
It shows the full lifecycle the Hub drives: discovery -> pairing -> commands -> teardown.

See the full guide at https://docs.majordom.io/device-integration.

A Controller bridges one external protocol/platform into the MajorDom language. The package exports
it from `peripherals(platform)` next to the server it needs (see `__init__.py`). The Hub gives it the
host (`self.platform`: its facts, the device repository and a documents folder), its settings
(`self.settings`) and its bound needs (`self.peripherals`) and calls the methods below; the controller
reports back to the Hub through `self.output` (a `ControllerOutput`).
"""

import asyncio
import contextlib
import logging
from urllib.parse import urlsplit
from uuid import UUID

from majordom_integration_sdk import (
    AbstractController,
    Device,
    DeviceCommand,
    Discovery,
    IntegrationError,
    Need,
    Parameter,
    Platform,
    ProvidedCredentials,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# What to report through `self.output` (see the docs):
# async def controller_did_receive_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_update_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_lose_discovery(self, controller: AbstractController, discovery_id: UUID): ...
# async def controller_did_connect_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_lose_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_receive_events(self, controller: AbstractController, events: Iterable[Event]): ...
# async def controller_did_encounter_error(self, controller: AbstractController, error: IntegrationError): ...
# async def controller_did_resolve_error(self, controller: AbstractController, error_id: str): ...
# async def controller_did_emit_notification(self, controller: AbstractController, notification: Notification): ...
# async def controller_did_change_provided(self, controller: AbstractController): ...  # what `provides` returns changed


class ExampleController(AbstractController[Device, Parameter, "ExampleController.Settings"]):
    """Bridges the Example protocol into MajorDom."""

    # Shown to the user, and its identity: its slug is the key the integration's devices, settings and folder are
    # kept by. Never rename it once released.
    name = "Example"

    # What the controller connects to beyond the network, and what the user can set. The Hub runs
    # `example_server()`, which the package provides next to it, binds the need to it and hands over
    # its URL in `self.peripherals.endpoint("example")`; settings arrive validated in `self.settings`.
    # Declare everything external as a Need: radios, Need("ble", ["router"]) (never raw Bluetooth),
    # Need("mdns", ["zeroconf"]), Need("upnp", ["ssdp"]) and the services you bring.
    # Leave them out if the protocol only uses the network.
    # See https://docs.majordom.io/device-integration/radios and .../settings.
    needs = [Need("example", ["echo"])]

    class Settings(BaseModel):
        # Give every field a default: the Hub builds the controller with them before the user can enter any
        server_name: str = Field(
            "MajorDom",
            pattern=r"^[^\r\n]+$",  # one line: it goes into the line protocol
            max_length=64,
            title="Server name",
            description="How the server introduces itself.",
        )

    _RECONNECT_DELAY = 1.0  # seconds, doubled after every failed attempt
    _RECONNECT_DELAY_MAX = 30.0

    def __init__(self, platform: Platform, *, settings: Settings | None = None):
        super().__init__(platform, settings=settings)
        self._discoveries: dict[UUID, Discovery] = {}
        # What start() sets up: stop() leaves them as here, also after a start that failed half-way
        self._writer: asyncio.StreamWriter | None = None  # to the server, while connected
        self._keeper: asyncio.Task[None] | None = None
        # e.g. self._cancel_zeroconf: Callable[[], None] | None = None

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only — never scan here.
        return self._discoveries

    # Lifecycle -------------------------------------------------------------

    async def start(self):
        # Register with discovery (needed as peripherals), subscribe to protocol events, and reconcile the
        # state of already-paired devices here.
        # e.g. async with self.platform.device_repository(self) as repository: paired = await repository.get_all()
        # e.g. with Need("mdns", ["zeroconf"]) in `needs`:
        # self._cancel_zeroconf = self.peripherals.instance("mdns").register(self, {"_example._tcp.local."})
        reader = await self._connect()  # raising here has the Hub retry start()
        self._keeper = asyncio.create_task(self._stay_connected(reader))

    async def stop(self):
        # Cancel tasks and release every held resource, also after a start that failed half-way: the Hub stops it then
        # too, and starts the same object again later.
        # e.g. if self._cancel_zeroconf:
        #     self._cancel_zeroconf()
        #     self._cancel_zeroconf = None
        if self._keeper:
            self._keeper.cancel()
            await asyncio.wait([self._keeper])  # unlike awaiting it, never raises (the keeper reports a crash itself)
            self._keeper = None
        self._disconnect()

    # Hooks: return True when applied in place, False to have the Hub restart the integration. The
    # defaults: settings_did_change and needed_peripheral_did_change (a need moved, or an optional one
    # appeared) restart it; platform_facts_did_change doesn't.

    async def settings_did_change(self, before: Settings) -> bool:
        if self.settings.server_name != before.server_name and self._writer:
            with contextlib.suppress(OSError):  # the server is away: the keeper hands it the name on reconnect
                await self._sync_with_server(self._writer)
        return True

    async def platform_facts_did_change(self, before: Platform) -> bool:
        # The server gets the region when the controller connects: let the Hub restart it for a new one
        return self.platform.region == before.region

    # Server ------------------------------------------------------------------

    async def _connect(self) -> asyncio.StreamReader:
        url = urlsplit(self.peripherals.endpoint("example").url)  # never build it yourself: the port may differ
        reader, self._writer = await asyncio.open_connection(url.hostname, url.port)
        await self._sync_with_server(self._writer)
        return reader

    def _disconnect(self):
        if self._writer:
            self._writer.close()
            self._writer = None

    async def _sync_with_server(self, writer: asyncio.StreamWriter):
        """Hands the server its configuration; on every (re)connect."""
        writer.write(f"name {self.settings.server_name}\n".encode())
        if region := self.platform.region:
            writer.write(f"region {region}\n".encode())
        await writer.drain()

    async def _stay_connected(self, reader: asyncio.StreamReader):
        """Reconnects whenever the server goes away (e.g. it was restarted) until stop() cancels it,
        so the integration heals by itself instead of being restarted by the Hub."""
        try:
            while True:
                await self._listen(reader)
                self._disconnect()
                reader = await self._reconnect()
        except Exception:  # a bug rather than an outage: the Hub restarts the integration, then gives up on it
            logger.exception(f"[{self.name}] stopped listening to the server")
            message = "The connection to the Example server broke unexpectedly."
            crashed = IntegrationError("crashed", message, is_still_running=False)
            await self.output.controller_did_encounter_error(self, crashed)

    async def _reconnect(self) -> asyncio.StreamReader:
        """Tries again, less and less often, until the server is back. Tells the user only once an attempt failed: a
        server restarting on purpose (e.g. recreated with new settings) is usually back by the first one."""
        delay, is_reported = self._RECONNECT_DELAY, False
        while True:
            await asyncio.sleep(delay)
            try:
                reader = await self._connect()
            except OSError as error:
                logger.info(f"[{self.name}] the server is not back yet: {error!r}")
                if not is_reported:
                    message = "Lost the connection to the Example server, reconnecting."
                    lost = IntegrationError("server-unreachable", message)
                    await self.output.controller_did_encounter_error(self, lost)
                    is_reported = True
                delay = min(delay * 2, self._RECONNECT_DELAY_MAX)
            else:
                if is_reported:
                    await self.output.controller_did_resolve_error(self, "server-unreachable")
                return reader

    async def _listen(self, reader: asyncio.StreamReader):
        """Reads the server's messages until it closes the connection."""
        with contextlib.suppress(OSError):
            while line := await reader.readline():
                # Turn protocol messages into events here: controller_did_receive_events(...)
                # Log and skip one you can't take: whatever raises here has the Hub restart the integration.
                logger.debug(f"[{self.name}] server: {line!r}")

    # Hub -> device ---------------------------------------------------------

    async def pair_device(self, discovery: Discovery, credentials: ProvidedCredentials | None):
        # Establish a session with the device, then report success to the Hub:
        # await self.output.controller_did_connect_device(self, self.device_uuid(...))
        # Keep what the protocol needs across restarts beyond the device database (keys, certificates)
        # in self.platform.documents_folder(self).
        raise NotImplementedError

    async def unpair(self, device: Device):
        raise NotImplementedError

    async def identify(self, device: Device):
        # Ask the device to blink/beep so the user can locate it.
        raise NotImplementedError

    async def fetch(self, device: Device):
        # Refresh the device and its parameters, reporting changes via
        # self.output.controller_did_receive_events(self, [...]).
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand, device: Device, parameter: Parameter):
        # Translate the MajorDom command into a protocol-level write.
        raise NotImplementedError
