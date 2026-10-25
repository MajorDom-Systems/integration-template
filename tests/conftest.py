"""Shared pytest fixtures for the whole suite live here.

conftest.py is auto-discovered by pytest — no import needed.

The fixtures wire the integration's Controller with the SDK's test doubles (a recording
`ControllerOutput`, an in-memory device repository, and fakes of every capability) and build
sample `Discovery`/`DeviceState` objects, so tests can drive the controller exactly as the
Hub would — without a running Hub.

**Device persistence is the Hub's core business logic, not the integration's.** The Hub
creates and stores device rows (name/room mapping, id assignment, the provisional→final id
reconciliation on pairing); an integration only reads through the injected repository and
writes parameter *state*. These fixtures therefore seed the repository the way the Hub
would, so the controller sees realistic state — the tests never make the integration
persist a device itself.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from majordom_integration_sdk import Endpoint
from majordom_integration_sdk.controller import Platform
from majordom_integration_sdk.peripherals import Peripherals
from majordom_integration_sdk.schemas.device import CredentialsType, Device, DeviceState, Discovery
from majordom_integration_sdk.schemas.parameter import (
    ParameterDataType,
    ParameterRole,
    ParameterState,
    ParameterVisibility,
)
from majordom_integration_sdk.testing import build_test_platform

from integration_template import ExampleController

INTEGRATION = ExampleController.name  # what the Hub scopes its devices by


class VirtualServer:
    """An in-process stand-in for `example_server()`: records the lines it receives and can go away."""

    def __init__(self) -> None:
        self.port = 0
        self.lines: list[str] = []
        self._server: asyncio.Server | None = None
        self._clients: list[asyncio.StreamWriter] = []

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", self.port)
        self.port = self._server.sockets[0].getsockname()[1]  # the same one again after a restart

    async def stop(self) -> None:
        for client in self._clients:
            client.close()
        self._clients.clear()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def received(self, line: str) -> None:
        async with asyncio.timeout(2):
            while line not in self.lines:
                await asyncio.sleep(0.01)

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self._clients.append(writer)
        with contextlib.suppress(ConnectionError):
            while line := await reader.readline():
                self.lines.append(line.decode().strip())


@pytest.fixture
async def server() -> AsyncIterator[VirtualServer]:
    server = VirtualServer()
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
def deps() -> Platform:
    """The SDK's test platform (recording output + in-memory repo), as the Hub gives it to every integration."""
    return build_test_platform()


@pytest.fixture
def peripherals(server: VirtualServer) -> Peripherals:
    """The controller's need bound to the virtual server, as the Hub binds it to `example_server()`."""
    return Peripherals({"example": Endpoint("example", "echo", f"tcp://127.0.0.1:{server.port}")})


@pytest.fixture
def controller(deps: Platform, peripherals: Peripherals) -> ExampleController:
    controller = ExampleController(deps)
    controller.peripherals = peripherals  # bound by hand, as in library mode
    return controller


# A virtual / simulated device — a fake endpoint that speaks your protocol in-process (no
# hardware, no network) so tests are deterministic and can assert what actually reached the
# device. Stand one up here and have the controller talk to it (e.g. via a base URL / mock
# transport injected through the controller). Tests then assert on both the controller's
# reports (deps.output) and this object's observed state.
#
# @pytest.fixture
# def virtual_device():
#     dev = VirtualExampleDevice()  # your in-process fake
#     dev.start()
#     yield dev
#     dev.stop()


async def _seed(deps: Platform, device: DeviceState) -> None:
    """Persist a device the way the Hub would, before handing control to the integration."""
    async with deps.make_device_repository(INTEGRATION) as repo:
        await repo.save(device)


@pytest.fixture
def discovery() -> Discovery:
    """A sample discovered-but-unpaired device (the controller surfaced this)."""
    return Discovery(
        id=uuid4(),
        integration=INTEGRATION,
        expected_credentials_options=[CredentialsType.none],
        transport="wifi",
        device_manufacturer="ACME",
        device_name="Example Lamp",
        device_category=None,
        device_icon=None,
    )


@pytest.fixture
async def provisional_device(deps: Platform, discovery: Discovery) -> DeviceState:
    """The device as it exists when the Hub calls `pair_device`.

    Before pairing, the Hub has already created the row from the user's input: name and room
    mapped, and its id set to the discovery's (still provisional) id — but no parameters yet;
    the controller discovers/maps those while pairing. After pairing the controller reports
    the real device id and the Hub reconciles the row. We seed the repository to match.
    """
    device = DeviceState(
        id=discovery.id,  # provisional id == discovery id, until pairing assigns the real one
        name="Living Room Lamp",  # mapped by the Hub from the user's input
        room_id=uuid4(),
        transport=discovery.transport,
        integration=INTEGRATION,
        manufacturer=discovery.device_manufacturer,
        parameters=[],
    )
    await _seed(deps, device)
    return device


@pytest.fixture
async def device_state(deps: Platform) -> DeviceState:
    """An already-paired device with one on/off parameter, as the Hub *stores* it (the full
    state, with parameters). Seeded into the repository."""
    power = ParameterState(
        id=uuid4(),
        name="Power",
        data_type=ParameterDataType.bool,
        role=ParameterRole.control,
        visibility=ParameterVisibility.user,
        integration_data=None,
        value=True,
    )
    state = DeviceState(
        id=uuid4(),
        name="Living Room Lamp",
        room_id=uuid4(),
        transport="wifi",
        integration=INTEGRATION,
        manufacturer="ACME",
        parameters=[power],
    )
    await _seed(deps, state)
    return state


@pytest.fixture
def device(device_state: DeviceState) -> Device:
    """The device as the Hub *passes* it to `fetch`/`identify`/`unpair`/`send_command` — a
    `Device` (info + integration_data), without the parameter list."""
    return Device.model_validate(device_state.model_dump())


@pytest.fixture
def parameter(device_state: DeviceState) -> ParameterState:
    """The target parameter for `send_command`, paired with `device`."""
    return device_state.parameters[0]
