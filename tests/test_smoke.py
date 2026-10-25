"""Basic tests that pass out of the box — they don't depend on protocol logic.

Kept separate from ``test_controller.py`` so the template repo's own CI (which excludes the
prefilled, expected-to-fail controller suite) still has tests to run and stays green.
"""

from majordom_integration_sdk import Service
from majordom_integration_sdk.testing import build_test_platform

from integration_template import ExampleController, peripherals


async def test_starts_and_stops(controller: ExampleController) -> None:
    await controller.start()
    await controller.stop()


async def test_name_and_slug(controller: ExampleController) -> None:
    assert controller.name == "Example"
    assert controller.name_slug == "example"


def test_exports_its_server_and_the_controller_that_needs_it():
    server, controller = peripherals(build_test_platform())
    assert isinstance(server, Service) and isinstance(controller, ExampleController)
    assert any(need.accepts(endpoint) for need in controller.needs for endpoint in server.provides)
