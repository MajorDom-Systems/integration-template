"""A minimal MajorDom integration controller.

This is a worked skeleton — replace the TODO bodies with real protocol calls. It shows the
full lifecycle the Hub drives: discovery -> pairing -> commands -> teardown.

See the full guide at https://docs.majordom.io/device-integration.

A Controller bridges one external protocol/platform into the MajorDom language. The Hub
instantiates it with the `Platform` and calls the methods below; the controller reports back
to the Hub through `self.output` (a `ControllerOutput`).
"""

from __future__ import annotations

from uuid import UUID

from majordom_integration_sdk import NoSettings, Platform
from majordom_integration_sdk.controller import AbstractController
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery, Parameter, ProvidedCredentials

# Output methods to call (see the docs):
# async def controller_did_receive_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_update_discovery(self, controller: AbstractController, discovery: Discovery): ...
# async def controller_did_lose_discovery(self, controller: AbstractController, discovery_id: UUID): ...
# async def controller_did_connect_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_lose_device(self, controller: AbstractController, device_id: UUID): ...
# async def controller_did_receive_events(self, controller: AbstractController, events: Iterable[Event]): ...


class ExampleController(AbstractController[Device, Parameter, NoSettings]):
    """Bridges the Example protocol into MajorDom."""

    def __init__(self, platform: Platform, *, settings: NoSettings | None = None):
        super().__init__(platform, settings=settings)
        self._discoveries: dict[UUID, Discovery] = {}

    name = "Example"

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only — never scan here.
        return self._discoveries

    # Lifecycle -------------------------------------------------------------

    async def start(self):
        # Register discovery services, subscribe to protocol events, and reconcile the
        # state of already-paired devices here.
        # e.g. self.peripherals.instance(ZEROCONF).add_listener("_example._tcp.local.", self)
        ...

    async def stop(self):
        # Cancel tasks and release every held resource.
        ...

    # Hub -> device ---------------------------------------------------------

    async def pair_device(
        self, discovery: Discovery, draft: DeviceState, credentials: ProvidedCredentials | None
    ) -> DeviceState:
        # The Hub built `draft`: the user's name, room and icon, the discovery's id. Fill it in and return it.
        # There is no record yet. Don't use the repository and don't report this device (no
        # `controller_did_connect_device`, no events): the Hub saves the draft, then reports it and calls `fetch`.
        #
        # 1. Give the device its final id from something unique to it (MAC, serial), never a name or an address two
        #    devices can share, and check it before anything irreversible:
        #        draft.id = self.device_uuid(serial)
        #        await self.check_device_id(draft.id, draft)  # raises DeviceIdTakenError when another record has it
        # 2. Fill the draft in place BEFORE each irreversible step (a key about to be set, a node about to be
        #    included). When pairing fails, the Hub calls `unpair(draft)` and it can only undo what the draft says ran:
        #        draft.integration_data = {"key": key}
        #        await device.set_key(key)
        # 3. Fill the rest (`parameters`, `available`) and return the draft.
        raise NotImplementedError

    async def unpair(self, device: Device):
        # Also the rollback of a failed pairing: `device` may be a half-filled draft (no final id, no
        # `integration_data`). Undo in reverse order of pairing, tolerate whatever is missing or gone, never wait for
        # the user, and go as far as you can: it is best effort and the Hub cuts it off after ~30 seconds.
        raise NotImplementedError

    async def identify(self, device: Device):
        # Ask the device to blink/beep so the user can locate it.
        raise NotImplementedError

    async def fetch(self, device: Device):
        # Idempotent: bring the device to a known-good state. Check it answers and read its current values, reporting
        # them via self.output.controller_did_receive_events(self, [...]). Check the event subscription and subscribe
        # again only if it is gone, never a second one. Finish in bounded time; a sleeping battery device that doesn't
        # answer is not a failure.
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand, device: Device, parameter: Parameter):
        # Translate the MajorDom command into a protocol-level write.
        raise NotImplementedError
