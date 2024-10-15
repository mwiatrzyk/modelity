import invoke


@invoke.task
def lint(ctx: invoke.Context):
    """Lint the code using various linting tools."""
    ctx.run("mypy modelity")


@invoke.task
def test(ctx: invoke.Context):
    """Run all tests."""
    ctx.run("pytest")


@invoke.task
def bump(ctx: invoke.Context):
    """Bump project version."""
    ctx.run("bumpify bump")


@invoke.task
def format(ctx: invoke.Context):
    """Run code formatting tools."""
    ctx.run("black --line-length=120 .")
