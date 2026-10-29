"""What the integration brings along: its server."""

from majordom_integration_sdk import Endpoint, Service
from pydantic import BaseModel, Field

# EXAMPLE: a tiny TCP echo server standing in for your protocol's server. Replace it; pin yours by digest.
IMAGE = "istio/tcp-echo-server:1.3@sha256:782259608d5ce934e1a07ce4a3f2664934b6806d50430fd20b7bf429ea500272"


class ServerSettings(BaseModel):
    """What the user can set on the server. They go into its compose, so a change recreates its container: the
    controller loses its connection and reconnects."""

    # Give every field a default: the server is built with them before the user can enter any
    greeting: str = Field(
        "hello",
        min_length=1,  # the server needs one: an empty value would leave the argument out
        title="Greeting",
        description="What the server puts before every line it echoes.",
    )


def example_server() -> Service[ServerSettings]:
    """A new one per call: the runtime keeps its state on the instance it runs."""
    return Service(
        "example-server",
        provides=[Endpoint("example", "echo", "tcp://127.0.0.1:{ports.api}")],
        settings=ServerSettings,
        ports={"api": 9000},  # preferred: the runtime picks another one when it's taken
        compose={
            "image": IMAGE,
            # Make yours listen on 127.0.0.1 only (e.g. zwave-js-server's `--host 127.0.0.1`): the Hub reaches it over
            # loopback, and nothing guards it on the LAN. This echo server can't choose its address.
            "network_mode": "host",
            "command": ["{ports.api}", "{settings.greeting}"],  # listens on the port the runtime picked
        },
    )
