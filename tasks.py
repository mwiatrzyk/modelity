import os

import invoke

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


@invoke.task
def lint(ctx: invoke.Context):
    """Lint the code using various linting tools."""
    ctx.run("mypy modelity")


@invoke.task
def test_docs(ctx: invoke.Context):
    """Test snippets from documentation."""
    ctx.run("sphinx-build -M doctest docs/source docs/build/html")


@invoke.task(test_docs)
def test(ctx: invoke.Context):
    """Run all tests."""
    ctx.run("pytest")


@invoke.task(lint, test)
def check(ctx):
    """Run all code quality checks."""


@invoke.task
def bump(ctx: invoke.Context):
    """Bump project version."""
    ctx.run("bumpify bump")


@invoke.task
def format(ctx: invoke.Context):
    """Run code formatting tools."""
    ctx.run("black --line-length=120 .")


@invoke.task
def build_docs(ctx: invoke.Context):
    """Build HTML documentation for Modelity."""
    ctx.run("sphinx-build -b html docs/source docs/build/html")


@invoke.task(build_docs)
def serve_docs(ctx: invoke.Context):
    """Build and serve HTML documentation for Modelity."""
    ctx.run("python -m http.server 8080 --directory docs/build/html")


@invoke.task()
def clean(ctx: invoke.Context, dry_run=False):
    """Clean the workspace."""
    extra_opts = "n" if dry_run else ""
    ctx.run(f"git clean -xdf{extra_opts} -e .python-version")
