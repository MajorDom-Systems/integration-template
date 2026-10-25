"""What the integration brings along: its server."""

from majordom_integration_sdk import Endpoint, Service

# EXAMPLE: a tiny TCP echo server standing in for your protocol's server. Replace it; pin yours by digest.
IMAGE = "istio/tcp-echo-server:1.3@sha256:782259608d5ce934e1a07ce4a3f2664934b6806d50430fd20b7bf429ea500272"


def example_server() -> Service:
    """A new one per call: the runtime keeps its state on the instance it runs."""
    return Service(
        "example-server",
        provides=[Endpoint("example", "echo", "tcp://127.0.0.1:{ports.api}")],
        ports={"api": 9000},  # preferred: the runtime picks another one when it's taken
        compose={
            "image": IMAGE,
            "network_mode": "host",
            "command": ["{ports.api}", "hello"],  # listens on the port the runtime picked
        },
    )
