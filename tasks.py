from invoke.tasks import task
from invoke.context import Context


@task
def lint(ctx: Context):
    """Lint the code using various linting tools."""
    ctx.run("mypy modelity")


@task(help={"report": "Report type. Run `pytest --help` for more details. Default: term"})
def coverage(ctx: Context, report: str = "term"):
    """Collect test coverage."""
    ctx.run(f"pytest --cov=modelity --cov-report={report}")


@task
def test_docs(ctx: Context):
    """Test snippets from documentation."""
    ctx.run("sphinx-build -M doctest docs/source docs/build/html")


@task(test_docs)
def test(ctx: Context):
    """Run all tests."""
    ctx.run("pytest")


@task(lint, test)
def check(ctx):
    """Run all code quality checks."""


@task
def format(ctx: Context):
    """Run code formatting tools."""
    ctx.run("black --line-length=120 .")


@task
def build_docs(ctx: Context):
    """Build HTML documentation for Modelity."""
    ctx.run("sphinx-build -b html docs/source docs/build/html")


@task(build_docs)
def serve_docs(ctx: Context):
    """Build and serve HTML documentation for Modelity."""
    ctx.run("python -m http.server 8080 --directory docs/build/html")


@task
def serve_coverage(ctx: Context, port: int = 9090):
    """Create HTML coverage report and serve it using local HTTP server."""
    ctx.run("inv coverage -r html:reports/coverage/html")
    ctx.run(f"python -m http.server {port} --directory reports/coverage/html")


@task
def clean(ctx: Context, dry_run=False):
    """Clean the workspace."""
    extra_opts = "n" if dry_run else ""
    ctx.run(f"git clean -xdf{extra_opts} -e .python-version")


@task
def gen_api_docs(ctx: Context):
    """Generate or update API docs sources from Modelity modules."""
    ctx.run("python scripts/generate_api_docs.py modelity/ docs/source/api/")
