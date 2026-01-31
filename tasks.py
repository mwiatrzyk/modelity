import os

import invoke

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


@invoke.task
def lint(ctx: invoke.Context):
    """Lint the code using various linting tools."""
    ctx.run("mypy modelity")


@invoke.task(help={"report": "Report type. Run `pytest --help` for more details. Default: term"})
def coverage(ctx: invoke.Context, report: str = "term"):
    """Collect test coverage."""
    ctx.run(f"pytest --cov=modelity --cov-report={report}")


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


@invoke.task
def serve_coverage(ctx: invoke.Context, port: int = 9090):
    """Create HTML coverage report and serve it using local HTTP server."""
    ctx.run("inv coverage -r html:reports/coverage/html")
    ctx.run(f"python -m http.server {port} --directory reports/coverage/html")


@invoke.task()
def clean(ctx: invoke.Context, dry_run=False):
    """Clean the workspace."""
    extra_opts = "n" if dry_run else ""
    ctx.run(f"git clean -xdf{extra_opts} -e .python-version")


@invoke.task()
def gen_api_docs(ctx: invoke.Context):
    """Generate or update API docs sources from Modelity modules."""
    ctx.run("python scripts/generate_api_docs.py modelity/ docs/source/api/")
