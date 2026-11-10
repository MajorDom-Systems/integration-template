"""A MajorDom integration controller template for an imaginary "acme" lamp.

Every method the Hub calls is here with its real signature, `raise NotImplementedError` right under it and, below that,
the code most likely to go in it, commented out, with hints. To implement a method:

1. delete its `raise NotImplementedError`,
2. uncomment its body (and the imports it needs, below) and change it to your protocol,
3. run its test in `tests/test_controller.py`.

The tests are the checklist: they fail on `NotImplementedError` until each method is done, and they pass against the
fake library in `acme.py` once its body is uncommented as it is. Swap `acme.py` for your protocol's library.

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

from integration_template.acme import AcmeClient

# Imports the commented bodies below need:
# import asyncio
# import secrets
# from contextlib import suppress
#
# from majordom_integration_sdk.schemas.device import CredentialsType
# from majordom_integration_sdk.schemas.event import DeviceParameterChange
# from majordom_integration_sdk.schemas.parameter import ParameterDataType, ParameterRole, ParameterState
# from majordom_integration_sdk.schemas.parameter import ParameterVisibility
#
# from integration_template.acme import AcmeError


class ExampleController(AbstractController[Device, Parameter, NoSettings]):
    """Bridges the Example protocol into MajorDom."""

    name = "Example"

    def __init__(self, platform: Platform, *, settings: NoSettings | None = None):
        super().__init__(platform, settings=settings)
        self.acme = AcmeClient()  # your protocol library's client
        self._discoveries: dict[UUID, Discovery] = {}
        self._addresses: dict[UUID, str] = {}  # where each discovery was found

    @property
    def discoveries(self) -> dict[UUID, Discovery]:
        # Return the cached snapshot only, never scan here.
        return self._discoveries

    # Types the Hub validates into -------------------------------------------

    # The defaults are fine until you keep typed `integration_data` or parameter data: then give the subclass here
    # (`class AcmeDevice(Device[AcmeData])`). With nothing to change, delete all three overrides, they only restate the
    # defaults.

    @property
    def device_type(self) -> type[Device]:
        raise NotImplementedError
        # return Device  # what `unpair`, `fetch`, `identify` and `send_command` are given

    @property
    def device_state_type(self) -> type[DeviceState]:
        raise NotImplementedError
        # return DeviceState  # what `pair_device` is given as its draft and returns

    @property
    def parameter_type(self) -> type[Parameter]:
        raise NotImplementedError
        # return Parameter  # what `send_command` is given

    # Lifecycle -------------------------------------------------------------

    async def start(self):
        raise NotImplementedError
        # await self.acme.open()
        # for lamp in await self.acme.scan():
        #     # A discovery id stays the same for the same device. It is not the final device id: that comes in
        #     # `pair_device`, from something unique to the device.
        #     discovery = Discovery(
        #         id=self.device_uuid(lamp.address),
        #         integration=self.key,
        #         expected_credentials_options=[CredentialsType.none],
        #         transport="wifi",
        #         device_manufacturer="ACME",
        #         device_name=f"Acme lamp {lamp.address}",
        #         device_category=None,
        #         device_icon=None,
        #     )
        #     self._discoveries[discovery.id] = discovery
        #     self._addresses[discovery.id] = lamp.address
        #     await self.output.controller_did_receive_discovery(self, discovery)
        # Real libraries push discoveries later: register a listener here and report `controller_did_receive_discovery`
        # and `controller_did_lose_discovery` from it. Also check the already-paired devices here (`fetch` each) and
        # report the ones that are gone with `controller_did_lose_device`. Raise when you can't start: it is retried.

    async def stop(self):
        raise NotImplementedError
        # await self.acme.close()
        # self._discoveries.clear()
        # self._addresses.clear()
        # Also called after a half-done `start`, and a `start` may follow: cancel tasks, close connections.

    # Hub -> device ---------------------------------------------------------

    async def start_pairing_window(self, duration_sec: int, credentials: ProvidedCredentials | None = None):
        raise NotImplementedError
        # await self.acme.open_pairing(duration_sec)
        # Only for protocols whose devices are not visible all the time (Zigbee permit-join, a BLE scan burst). When
        # yours always are, delete this method and its test: the base class does nothing.

    async def pair_device(
        self, discovery: Discovery, draft: DeviceState, credentials: ProvidedCredentials | None
    ) -> DeviceState:
        raise NotImplementedError
        # The Hub built `draft` from the user's form and saves what you return. So no device repository in here and no
        # `controller_did_connect_device`, no events: the Hub reports the device after it saved it, then calls `fetch`.
        # When the device needs credentials the Hub lacks, raise `MissingCredentialsError` before touching it.
        #
        # lamp = await self.acme.connect(self._addresses[discovery.id])
        #
        # The final id comes from a string unique to this device (serial, MAC). A name or an address two devices can
        # share would give them one id. Check it before anything irreversible: it raises `DeviceIdTakenError` when
        # another record holds it, and the Hub answers the user with that. Set `draft.id` only after the check: until
        # then it names the record the user picked, which is not "another" one.
        # device_id = self.device_uuid(lamp.serial)
        # await self.check_device_id(device_id, draft)
        # draft.id = device_id
        #
        # Fill the draft BEFORE each irreversible step, so what you hold always says what ran.
        # key = secrets.token_hex(16)
        # draft.integration_data = {"serial": lamp.serial, "address": lamp.address, "key": key}
        # try:
        #     await lamp.set_key(key)
        #     power = ParameterState(
        #         id=self.parameter_uuid(draft.id, "power"),
        #         name="Power",
        #         data_type=ParameterDataType.bool,
        #         role=ParameterRole.control,
        #         visibility=ParameterVisibility.user,
        #         integration_data=None,
        #         value=(await lamp.read())["power"],
        #     )
        #     draft.parameters = [power]
        #     draft.available = True
        # except Exception:
        #     # On a failure undo only what would block a retry: the key we set and now lose would lock us out of the
        #     # lamp. Keep what a retry reuses (a Wi-Fi join, a bond). `unpair` is not called: it is the user's removal.
        #     with suppress(AcmeError):
        #         await lamp.clear_key()
        #     raise
        # Subscribe in `fetch`, not here: the Hub calls it right after the save.
        # return draft

    async def unpair(self, device: Device):
        raise NotImplementedError
        # The user removed the device. Undo in reverse order of pairing and tolerate any state: a half-filled record
        # (no `integration_data`), a lamp that is gone or was reset. Never wait for the user, never raise for a lamp
        # that isn't there. The Hub removes the record itself.
        # data = device.integration_data or {}
        # if "key" not in data:
        #     return
        # with suppress(AcmeError):
        #     lamp = await self.acme.connect(data["address"], data["key"])
        #     await lamp.unsubscribe(str(device.id))
        #     await lamp.clear_key()

    async def identify(self, device: Device):
        raise NotImplementedError
        # Make the device blink or beep so the user can find it.
        # data = device.integration_data
        # lamp = await self.acme.connect(data["address"], data["key"])
        # await lamp.blink()

    async def fetch(self, device: Device):
        raise NotImplementedError
        # Called after pairing, on a manual refresh and to revive an unavailable device, so it must be safe to repeat:
        # check the device answers, read its values, subscribe only if the subscription is gone (never a second one).
        # Report only what was read.
        # data = device.integration_data
        # token = str(device.id)
        # try:
        #     async with asyncio.timeout(10):
        #         lamp = await self.acme.connect(data["address"], data["key"])
        #         values = await lamp.read()
        # except (AcmeError, TimeoutError):
        #     return  # A sleeping or offline device is not a failure: report nothing, the last known state stays.
        # if token not in lamp.subscriptions:
        #     await lamp.subscribe(token)  # A real library takes a callback here, reporting changes as events.
        # change = DeviceParameterChange(
        #     device_id=device.id, parameter_id=self.parameter_uuid(device.id, "power"), value=values["power"]
        # )
        # await self.output.controller_did_receive_events(self, [change])

    async def send_command(self, command: DeviceCommand, device: Device, parameter: Parameter):
        raise NotImplementedError
        # Translate the MajorDom command into a protocol write. `parameter.id` tells which parameter it is: map it
        # back with the same `parameter_uuid` call you made in `pair_device` when you have several.
        # data = device.integration_data
        # lamp = await self.acme.connect(data["address"], data["key"])
        # await lamp.set_power(command.value)
        # Report the new value yourself only when the device doesn't announce it through its subscription.
