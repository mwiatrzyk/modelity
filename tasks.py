import invoke


@invoke.task
def test(ctx: invoke.Context):
    """Run all tests."""
    ctx.run("pytest")


@invoke.task
def format(ctx: invoke.Context):
    """Run code formatting tools."""
    ctx.run("black --line-length=123 .")
