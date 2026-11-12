"""A MajorDom integration controller skeleton to fill.

Every method the Hub calls is here with its real signature, a placeholder body and, above it, a checklist of what the
SDK expects from it. Replace each placeholder with your protocol's calls and fill the matching test in
`tests/test_controller.py`: the tests fail until each method is done.

A Controller bridges one external protocol into MajorDom. The Hub instantiates it with the `Platform` and calls the
methods below; the controller reports back through `self.output` (a `ControllerOutput`): discoveries, devices that
connected or were lost, events. Full guide: https://docs.majordom.io/device-integration
"""

from __future__ import annotations

from uuid import UUID

from majordom_integration_sdk import NoSettings, Platform
from majordom_integration_sdk.controller import AbstractController
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery, Parameter, ProvidedCredentials

# Output methods to call (ids are keyword-only: integrations pass `physical_id=`):
# await self.output.controller_did_receive_discovery(self, discovery)
# await self.output.controller_did_update_discovery(self, discovery)
# await self.output.controller_did_lose_discovery(self, discovery_id)
# await self.output.controller_did_connect_device(self, physical_id=physical_id)
# await self.output.controller_did_lose_device(self, physical_id=physical_id)
# await self.output.controller_did_receive_events(self, events)  # e.g. DeviceParameterChange(physical_id=..., ...)


class ExampleController(AbstractController[Device, Parameter, NoSettings]):
    """Bridges the Example protocol into MajorDom."""

    name = "Example"

    def __init__(self, platform: Platform, *, settings: NoSettings | None = None):
        super().__init__(platform, settings=settings)
        self._discoveries: dict[UUID, Discovery] = {}

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only, never scan here.
        return self._discoveries

    # Types the Hub validates into -------------------------------------------

    # The defaults are fine until you keep typed `integration_data` or parameter data: then return your subclass
    # (`class MyDevice(Device[MyData])`). With nothing to change, delete all three overrides.

    @property
    def device_type(self) -> type[Device]:
        return Device  # what `unpair`, `fetch`, `identify` and `send_command` are given

    @property
    def device_state_type(self) -> type[DeviceState]:
        return DeviceState  # what `pair_device` is given as its draft and returns

    @property
    def parameter_type(self) -> type[Parameter]:
        return Parameter  # what `send_command` is given

    # Lifecycle -------------------------------------------------------------

    async def start(self):
        # - Open your protocol's client and register discovery listeners; report discoveries as they come and go.
        # - A discovery id stays the same for the same device; it is not the device's `physical_id`.
        # - Check the already-paired devices (`fetch` each); report the gone ones with
        #   `controller_did_lose_device(self, physical_id=...)`.
        # - Raise when you can't start: it is retried.
        ...

    async def stop(self):
        # Also called after a half-done `start`, and a `start` may follow: cancel tasks, close connections.
        ...

    # Hub -> device ---------------------------------------------------------

    async def start_pairing_window(self, duration_sec: int, credentials: ProvidedCredentials | None = None):
        # Only for protocols whose devices are not visible all the time (Zigbee permit-join, a BLE scan burst). When
        # yours always are, delete this method and its test: the base class does nothing.
        raise NotImplementedError

    async def pair_device(
        self, discovery: Discovery, draft: DeviceState, credentials: ProvidedCredentials | None
    ) -> DeviceState:
        # - The Hub built `draft` from the user's form and saves what you return: no device repository here, and no
        #   `controller_did_connect_device` or events. The Hub reports the device after the save, then calls `fetch`.
        # - Raise `MissingCredentialsError` before touching the device when it needs credentials the Hub lacks.
        # - `draft.id` is the Hub's: never change it. Set `draft.physical_id = self.device_uuid(...)` from a string
        #   unique to the device (serial, MAC), then `await self.check_device_id(draft.physical_id, draft)` before
        #   anything irreversible: it raises `DeviceIdTakenError` when another record holds it.
        # - Fill `draft.integration_data` BEFORE each irreversible step: it is saved with the device and `unpair`
        #   rolls back from it. No storage files of your own.
        # - Fill `parameters` (ids from `self.parameter_uuid(draft.physical_id, ...)`) and `available`, return `draft`.
        # - On any failure but `DeviceIdTakenError`, and when its save fails, the Hub calls `unpair(draft)` to roll
        #   back: don't undo here.
        # - Idempotent, like `fetch`: a retry after a failed or rolled-back attempt reaches a known-good paired state
        #   from whatever the last one left, confirming what is already done instead of refusing it.
        # - Subscribe in `fetch`, not here.
        raise NotImplementedError

    async def unpair(self, device: Device):
        # - The user's removal, and the Hub's rollback of a failed pairing (with the draft as `pair_device` left it).
        # - Undo in reverse order of pairing only what blocks a clean re-pair (a key set on the device, a pairing the
        #   device holds). Harmless leftovers (a node left on the network, offered again as a discovery) need no undo.
        # - Tolerate any stage (no `integration_data` yet, a device already reset), never wait for the user, best
        #   effort within the Hub's 30 s, and safe to call again. The Hub removes the record itself.
        # - When the device can't be reached to undo its pairing: forget your own state of it, then raise
        #   `DeviceUnreachableError`.
        raise NotImplementedError

    async def identify(self, device: Device):
        # Make the device blink or beep so the user can find it.
        raise NotImplementedError

    async def fetch(self, device: Device):
        # Called after pairing, on a manual refresh and to revive an unavailable device, so it must be safe to repeat:
        # - check the device answers and read its values, reported as events by `physical_id`;
        # - subscribe only if the subscription is gone, never a second one;
        # - finish in bounded time; a sleeping or offline device is not a failure: report nothing.
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand, device: Device, parameter: Parameter):
        # Translate the MajorDom command into a protocol write; `parameter.id` tells which parameter it is. Report the
        # new value yourself only when the device doesn't announce it through its subscription.
        raise NotImplementedError
