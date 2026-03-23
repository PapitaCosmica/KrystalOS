"""
KrystalOS — cli/main.py
Root Typer application. Registers all krystal-commander commands.
"""

from __future__ import annotations

import typer
from rich.console import Console

from cli.commands.init import init_project
from cli.commands.make_widget import make_widget
from cli.commands.doctor import run_doctor
from cli.commands.dev_guide import show_dev_guide
from cli.commands.install import install_widget, update_widget
from cli.commands.serve import serve_app
from cli.bundler import bundle_app
from cli.deployer import deploy_app

app = typer.Typer(
    name="krystal",
    help=(
        "🔷  [bold cyan]KrystalOS Commander[/] — "
        "Modular micro-services orchestrator CLI."
    ),
    rich_markup_mode="rich",
    add_completion=True,
    no_args_is_help=True,
)

console = Console()


# ---------------------------------------------------------------------------
# krystal init <name>
# ---------------------------------------------------------------------------

@app.command("init")
def cmd_init(
    name: str = typer.Argument(..., help="Project name / directory to create"),
) -> None:
    """
    🏗  Scaffold a new KrystalOS project.

    Creates the standard directory layout (cli/, core/, widgets/, shared/,
    .krystal/) and a global [bold]krystal.config.json[/].
    """
    init_project(name)


# ---------------------------------------------------------------------------
# krystal make:widget
# ---------------------------------------------------------------------------

@app.command("make:widget")
def cmd_make_widget() -> None:
    """
    🧩  Interactive wizard to generate a new widget.

    Prompts for name, language, version and grid size, then scaffolds the
    widget folder with a validated [bold]krystal.json[/], a language
    starter file, and a Tailwind Glassmorphism [bold]ui.html[/].
    """
    make_widget()


# ---------------------------------------------------------------------------
# krystal doctor
# ---------------------------------------------------------------------------

@app.command("doctor")
def cmd_doctor(
    bundle: bool = typer.Option(
        False,
        "--bundle",
        help="(Phase 4) Prepare portable binary bundles for Lite Mode.",
    ),
) -> None:
    """
    🩺  Run hardware & software diagnostics.

    Reports RAM, CPU, and PATH availability for php, python, node and
    docker. Suggests Lite Mode if available RAM is below 4 GB.
    """
    run_doctor(bundle=bundle)


# ---------------------------------------------------------------------------
# krystal install <url>
# ---------------------------------------------------------------------------

@app.command("install")
def cmd_install(
    url: str = typer.Argument(
        ..., help="GitHub URL of the widget to install."
    ),
) -> None:
    """
    📦  Install a widget from the Krystal Market ecosystem.
    
    Downloads the widget repository and scans it with the Sandbox Guard.
    """
    install_widget(url)

# ---------------------------------------------------------------------------
# krystal update <name>
# ---------------------------------------------------------------------------

@app.command("update")
def cmd_update(
    name: str = typer.Argument(
        ..., help="Name of the installed widget to update."
    ),
) -> None:
    """
    🔄  Update an installed widget from its external repository.
    """
    update_widget(name)


# ---------------------------------------------------------------------------
# krystal dev-guide
# ---------------------------------------------------------------------------

@app.command("dev-guide")
def cmd_dev_guide() -> None:
    """
    📚  Read the KrystalOS Developer Guide for making widgets.
    """
    show_dev_guide()

# ---------------------------------------------------------------------------
# krystal serve (Command Group)
# ---------------------------------------------------------------------------
app.add_typer(serve_app, name="serve")

# ---------------------------------------------------------------------------
# krystal bundle (Command Group)
# ---------------------------------------------------------------------------
app.add_typer(bundle_app, name="bundle")

# ---------------------------------------------------------------------------
# krystal deploy (Command Group)
# ---------------------------------------------------------------------------
app.add_typer(deploy_app, name="deploy")

# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
