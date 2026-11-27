"""integration_template — rename this package to majordom_<protocol> (see README).

Exports `peripherals(platform)`, the entry point the Hub (or the SDK's standalone dev runner,
`run_controller(integration_template.peripherals)`) runs: the integration's controller and the
server it needs.
"""

from majordom_integration_sdk import Peripheral, Platform

from integration_template.config import example_server
from integration_template.controller import ExampleController


def peripherals(platform: Platform) -> list[Peripheral]:
    """The server runs while the controller, which needs it, does."""
    return [example_server(), ExampleController(platform)]


__all__ = ["ExampleController", "peripherals"]
