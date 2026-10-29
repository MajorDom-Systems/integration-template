"""Basic tests that pass out of the box — they don't depend on protocol logic.

Kept separate from ``test_controller.py`` so the template repo's own CI (which excludes the
prefilled, expected-to-fail controller suite) still has tests to run and stays green.
"""

from majordom_integration_sdk import Discovery, Platform, Service

from integration_template import ExampleController, peripherals


async def test_starts_and_stops(controller: ExampleController):
    await controller.start()
    await controller.stop()


async def test_forgets_its_discoveries_when_it_stops(controller: ExampleController, discovery: Discovery):
    await controller.start()
    controller._discoveries[discovery.id] = discovery  # as your discovery listener caches it
    await controller.stop()
    assert controller.discoveries == {}  # the device may be gone or paired elsewhere by the next start


async def test_name_and_key(controller: ExampleController):
    assert controller.name == "Example"
    assert controller.key == "example"  # what its devices, settings and folder are kept by


def test_exports_its_server_and_the_controller_that_needs_it(platform: Platform):
    server, controller = peripherals(platform)
    assert isinstance(server, Service) and isinstance(controller, ExampleController)
    assert any(need.accepts(endpoint) for need in controller.needs for endpoint in server.provides)
