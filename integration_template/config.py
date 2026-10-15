"""What the integration brings along (its server) and what the user can set."""

from majordom_integration_sdk import Endpoint, Service
from pydantic import BaseModel, Field


class ExampleSettings(BaseModel):
    server_name: str = Field("MajorDom", title="Server name", description="How the server introduces itself.")


EXAMPLE_SERVER = Service(
    "example-server",
    provides=[Endpoint("example", "tcp", "tcp://127.0.0.1:{ports.api}")],
    ports={"api": 9000},  # preferred: the runtime picks another one when it's taken
    compose={
        # EXAMPLE: a tiny TCP echo server standing in for your protocol's server. Replace it; pin yours by digest.
        "image": "istio/tcp-echo-server:1.3@sha256:782259608d5ce934e1a07ce4a3f2664934b6806d50430fd20b7bf429ea500272",
        "network_mode": "host",
        "command": ["{ports.api}", "hello"],  # listens on the port the runtime picked
    },
)
