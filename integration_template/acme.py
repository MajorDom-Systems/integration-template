"""A tiny fake of an imaginary "acme" lamp library, so the commented-out bodies in `controller.py` can run in the tests.

Delete it with your first real protocol library: `AcmeClient` stands for the library's client and `AcmeLamp` for the
device on the other end. The tests use `AcmeLamp` as the virtual device: they set it up and check what reached it.
"""


class AcmeError(Exception):
    """The library's own error: the lamp is offline, refused the key or the read."""


class AcmeLamp:
    def __init__(self, serial: str, address: str, *, online: bool = True):
        self.serial = serial
        self.address = address
        self.online = online
        self.read_fails = False
        self.key: str | None = None
        self.power = True
        self.blinks = 0
        self.subscriptions: list[str] = []  # a second `subscribe` with the same token adds a second one

    def _check_online(self):
        if not self.online:
            raise AcmeError(f"{self.address} does not answer")

    async def set_key(self, key: str):
        self._check_online()
        self.key = key

    async def clear_key(self):
        self._check_online()
        self.key = None

    async def read(self) -> dict[str, bool]:
        self._check_online()
        if self.read_fails:
            raise AcmeError("read failed")
        return {"power": self.power}

    async def set_power(self, value: bool):
        self._check_online()
        self.power = value

    async def blink(self):
        self._check_online()
        self.blinks += 1

    async def subscribe(self, token: str):
        self._check_online()
        self.subscriptions.append(token)

    async def unsubscribe(self, token: str):
        self._check_online()
        self.subscriptions = [subscription for subscription in self.subscriptions if subscription != token]


class AcmeClient:
    def __init__(self, lamps: list[AcmeLamp] | None = None):
        self.lamps = lamps or []
        self.is_open = False
        self.pairing_open = False

    async def open(self):
        self.is_open = True

    async def close(self):
        self.is_open = False

    async def scan(self) -> list[AcmeLamp]:
        if not self.is_open:
            raise AcmeError("client is not open")
        return [lamp for lamp in self.lamps if lamp.online]

    async def open_pairing(self, duration_sec: int):
        self.pairing_open = True

    async def connect(self, address: str, key: str | None = None) -> AcmeLamp:
        """A lamp that holds a key only talks to whoever knows it; an unkeyed one accepts anyone."""
        lamp = next((lamp for lamp in self.lamps if lamp.address == address), None)
        if lamp is None or not lamp.online:
            raise AcmeError(f"{address} does not answer")
        if lamp.key is not None and key != lamp.key:
            raise AcmeError(f"{address} refused the key")
        return lamp
