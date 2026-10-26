"""What the tests run the controller against, in place of the server the integration brings."""

import asyncio
import contextlib


class VirtualServer:
    """An in-process stand-in for `example_server()`: records the lines it receives and can go away."""

    def __init__(self):
        self.port = 0
        self.lines: list[str] = []
        self._server: asyncio.Server | None = None
        self._clients: set[asyncio.StreamWriter] = set()  # the connected ones

    async def start(self):
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", self.port)
        self.port = self._server.sockets[0].getsockname()[1]  # the same one again after a restart

    async def stop(self):
        for client in self._clients:
            client.close()
        self._clients.clear()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    @property
    def is_connected(self) -> bool:
        return bool(self._clients)

    async def send(self, line: bytes):
        for client in [*self._clients]:  # one may go while another drains
            client.write(line + b"\n")
            await client.drain()

    async def received(self, line: str):
        async with asyncio.timeout(2):
            while line not in self.lines:
                await asyncio.sleep(0.01)

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._clients.add(writer)
        try:
            with contextlib.suppress(ConnectionError):
                while line := await reader.readline():
                    self.lines.append(line.decode().strip())
        finally:  # the client went: stop writing to it
            self._clients.discard(writer)
            writer.close()
