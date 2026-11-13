"""A MajorDom integration controller skeleton to fill.

A controller puts one IoT protocol behind the single standard facade every MajorDom integration shares. It works on
its own: as a library in any Python app, from the SDK's standalone CLI, or inside the MajorDom Hub. Whoever drives it
calls the methods below and hears back through `self.output` (a `ControllerOutput`): discoveries, devices that
connected or were lost, events.

Every method is here with its real signature, a placeholder body and a checklist of what the SDK expects from it.
Replace each placeholder with your protocol's calls and fill the matching test in `tests/test_controller.py`: the
tests fail until each method is done. Full guide: https://docs.majordom.io/device-integration
"""

from __future__ import annotations

from uuid import UUID

from majordom_integration_sdk import Need, Platform
from majordom_integration_sdk.controller import AbstractController
from majordom_integration_sdk.schemas.command import DeviceCommand
from majordom_integration_sdk.schemas.device import Device, DeviceState, Discovery, Parameter, ProvidedCredentials
from pydantic import BaseModel

# Output methods to call (ids are keyword-only: integrations pass `physical_id=`):
# await self.output.controller_did_receive_discovery(self, discovery)
# await self.output.controller_did_update_discovery(self, discovery)
# await self.output.controller_did_lose_discovery(self, discovery_id)
# await self.output.controller_did_connect_device(self, physical_id=physical_id)
# await self.output.controller_did_lose_device(self, physical_id=physical_id)
# await self.output.controller_did_receive_events(self, [
#     DeviceParameterChange(physical_id=physical_id, parameter_id=self.parameter_uuid(physical_id, "..."), value=...),
# ])
# await self.output.controller_did_encounter_error(self, IntegrationError("server-unreachable", "..."))
# await self.output.controller_did_resolve_error(self, "server-unreachable")


# Your own data, typed: the controller gets every device and parameter already parsed into these classes.


class ExampleDeviceData(BaseModel):
    """What you keep about a paired device in `integration_data`: an address, a key set on it, …"""


class ExampleParameterData(BaseModel):
    """What you keep about a parameter in its `integration_data`: the protocol's attribute or endpoint, …"""


class ExampleDevice(Device[ExampleDeviceData]): ...


class ExampleDeviceState(DeviceState[ExampleDeviceData, ExampleParameterData]): ...


class ExampleParameter(Parameter[ExampleParameterData]): ...


class ExampleController(
    AbstractController[ExampleDevice, ExampleParameter, "ExampleController.Settings", ExampleDeviceState]
):
    """Bridges the Example protocol into MajorDom."""

    # Everything external beyond the network: the server from `config.py`, radios, the SDK's BLE_ROUTER, ZEROCONF,
    # UPNP_SSDP. Delete the ones you don't use, and the list when the protocol only uses the network.
    needs = [Need("example", ["example"])]

    class Settings(BaseModel):
        """What the user can set on the controller, validated into `self.settings`. Give every field a default: the
        controller is built with them before the user can enter any. Use `NoSettings` instead when there are none."""

    def __init__(self, platform: Platform, *, settings: Settings | None = None):
        super().__init__(platform, settings=settings)
        self._discoveries: dict[UUID, Discovery] = {}

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only, never scan here.
        return self._discoveries

    # Your types, which every call's arguments are parsed into ------------------

    @property
    def device_type(self) -> type[ExampleDevice]:
        return ExampleDevice  # what `unpair`, `fetch`, `identify` and `send_command` are given

    @property
    def device_state_type(self) -> type[ExampleDeviceState]:
        return ExampleDeviceState  # what `pair_device` is given as its draft and returns

    @property
    def parameter_type(self) -> type[ExampleParameter]:
        return ExampleParameter  # what `send_command` is given

    # Lifecycle -------------------------------------------------------------

    async def start(self):
        # - Connect to your server through `self.peripherals.endpoint("example").url`, never a URL of your own: the
        #   port may differ. Raise when you can't: `start` is retried.
        # - Once connected, stay connected by yourself: reconnect with a growing delay when the server goes away, and
        #   report it with `controller_did_encounter_error` only when it stays away, resolving it when it is back.
        # - Open your protocol's client and register discovery listeners; report discoveries as they come and go.
        # - A discovery id stays the same for the same device; it is not the device's `physical_id`.
        # - Check the already-paired devices (`fetch` each); report the gone ones with
        #   `controller_did_lose_device(self, physical_id=...)`.
        ...

    async def stop(self):
        # Also called after a half-done `start`, and a `start` may follow: cancel tasks, close connections, clear
        # `self._discoveries` (they are heard anew after the next start).
        ...

    # Return True when applied in place, False to have the runtime restart the controller.

    async def settings_did_change(self, before: Settings) -> bool:
        return False

    async def platform_facts_did_change(self, before: Platform) -> bool:
        # e.g. return False when the region changed and your server needs it on connect
        return True

    # Hub -> device ---------------------------------------------------------

    async def start_pairing_window(self, duration_sec: int, credentials: ProvidedCredentials | None = None):
        # Only for protocols whose devices are not visible all the time (Zigbee permit-join, a BLE scan burst). When
        # yours always are, delete this method and its test: the base class does nothing.
        raise NotImplementedError

    async def pair_device(
        self, discovery: Discovery, draft: ExampleDeviceState, credentials: ProvidedCredentials | None
    ) -> ExampleDeviceState:
        # - The Hub built `draft` from the user's form and saves what you return: no device repository here, and no
        #   `controller_did_connect_device` or events. The Hub reports the device after the save, then calls `fetch`.
        # - Raise `MissingCredentialsError` before touching the device when it needs credentials the Hub lacks.
        # - `draft.id` is the Hub's: never change it. Set `draft.physical_id = self.device_uuid(...)` from a string or
        #   bytes unique to the device (serial, MAC). Build it in one place (a single id-making method), never
        #   assembled anew at each call site.
        # - Then `await self.check_device_id(draft.physical_id, draft)` before anything irreversible: it confirms no
        #   other record holds this device already, and raises `DeviceIdTakenError` when one does.
        # - Fill `draft.integration_data` BEFORE each irreversible step: it is saved with the device and `unpair`
        #   rolls back from it. No storage files of your own.
        # - Set `available` and return `draft`. Leave `parameters` empty: `fetch` reads them right after the save.
        # - Just raise on failure: on any failure but `DeviceIdTakenError`, and when its save fails, the Hub calls
        #   `unpair(draft)`, which undoes the partial pairing.
        # - Idempotent: a retry after a failed or rolled-back attempt reaches a known-good paired state from whatever
        #   the last one left, confirming what is already done instead of refusing it.
        # - Don't map parameters, read values or subscribe here: the Hub calls `fetch` for that right after the save.
        raise NotImplementedError

    async def unpair(self, device: ExampleDevice):
        # - The user's removal, and the Hub's rollback of a failed pairing (with the draft as `pair_device` left it).
        # - Undo everything pairing did, in reverse order: a key set on the device, the pairing it holds, its place on
        #   the network.
        # - Tolerate any stage (no `integration_data` yet, a device already reset), never wait for the user, best
        #   effort within the Hub's 30 s, and safe to call again.
        # - Talk to the device only: the Hub alone decides whether to delete the record and its `integration_data`.
        #   When the device can't be reached, raise `DeviceUnreachableError` and change nothing else.
        raise NotImplementedError

    async def identify(self, device: ExampleDevice):
        # Make the device blink or beep so the user can find it.
        raise NotImplementedError

    async def fetch(self, device: ExampleDevice) -> ExampleDeviceState | None:
        # Called right after pairing, on a manual refresh and to revive an unavailable device, so it must be safe to
        # repeat:
        # - read the whole device and return it: `ExampleDeviceState(**device.model_dump(), parameters=[...])` with
        #   every parameter (ids from `self.parameter_uuid(device.physical_id, ...)`) and its current value, and
        #   `available`. The Hub compares it with what it stored; report none of it as events: those are for changes
        #   the device starts itself;
        # - subscribe only if the subscription is gone, never a second one;
        # - finish in bounded time; return `None` when the device doesn't answer (sleeping, offline): not a failure.
        raise NotImplementedError

    async def send_command(self, command: DeviceCommand, device: ExampleDevice, parameter: ExampleParameter):
        # Translate the MajorDom command into a protocol write; `parameter.id` tells which parameter it is. Report the
        # new value yourself only when the device doesn't announce it through its subscription.
        raise NotImplementedError
