"""What the integration brings along: the server its protocol needs (e.g. zwave-js-server, a matter.js server).

Delete this file and its use in `__init__.py` when your controller talks to devices directly. Worked example:
https://docs.majordom.io/integrations/server-example
"""

from majordom_integration_sdk import Endpoint, Service
from pydantic import BaseModel

IMAGE = "TODO/your-server:1.0@sha256:TODO"  # pin by digest


class ServerSettings(BaseModel):
    """What the user can set on the server: each field goes into its compose, so a change recreates the container.
    Give every field a default: the server is built with them before the user can enter any."""


def example_server() -> Service[ServerSettings]:
    """A new one per call: the runtime keeps its state on the instance it runs."""
    return Service(
        "example-server",
        # What it offers the controller: the controller's `Need("example", ["example"])` binds to it
        provides=[Endpoint("example", "example", "tcp://127.0.0.1:{ports.api}")],
        settings=ServerSettings,
        ports={"api": 9000},  # preferred: the runtime picks another one when it's taken
        compose={
            "image": IMAGE,
            "network_mode": "host",
            # Make it listen on 127.0.0.1 and on the port the runtime picked: nothing guards it on the LAN
            "command": ["TODO", "{ports.api}"],
        },
    )
