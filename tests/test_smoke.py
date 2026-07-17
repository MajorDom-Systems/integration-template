"""Basic tests that pass out of the box — they don't depend on protocol logic.

Kept separate from ``test_controller.py`` so the template repo's own CI (which excludes the
prefilled, expected-to-fail controller suite) still has tests to run and stays green.
"""


async def test_starts_and_stops(controller):
    await controller.start()
    await controller.stop()


async def test_name_and_slug(controller):
    assert controller.name == "Example"
    assert controller.name_slug == "example"
