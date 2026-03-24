"""
KrystalOS — cli/main.py
Root Typer application. Registers all krystal-commander commands.
"""

from __future__ import annotations

import typer
from rich.console import Console

from cli.commands.init import init_project
from cli.factory import scaffolding_wizard
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
    """
    init_project(name)


# ---------------------------------------------------------------------------
# krystal env:set <target>
# ---------------------------------------------------------------------------
from cli.commands.init import set_env

@app.command("env:set")
def cmd_env_set(
    target: str = typer.Argument(
        ..., help="Forza el modo del Workspace actual (LITE o PRO)."
    ),
) -> None:
    """
    ⚙️  Force the KrystalOS Workspace Target Environment.
    """
    set_env(target)


# ---------------------------------------------------------------------------
# krystal make:widget
# ---------------------------------------------------------------------------

@app.command("make:widget")
def cmd_make_widget(
    test: bool = typer.Option(False, "--test", help="Generates an isolated UI/Events Lab for this Widget")
) -> None:
    """
    🧩  Interactive wizard to generate a new standalone widget.
    
    Prompts for architecture (MVC/Simple/AI), language, and generates 
    the autonomous standalone environment via The Factory.
    If --test is passed, creates a Krystal Lab.
    """
    if test:
        from cli.lab_engine import deploy_lab
        # Assuming widget name is prompted inside scaffold, but for --test we might want to bypass or ask
        name = typer.prompt("¿Cómo se llama tu Widget Lab?", default="my-widget-lab")
        deploy_lab("widget", name.replace(" ", "-").lower())
        return
        
    scaffolding_wizard()

# ---------------------------------------------------------------------------
# krystal make:mod
# ---------------------------------------------------------------------------
from cli.commands.mod_scaffolder import make_mod
app.command("make:mod")(make_mod)


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
# krystal test:all
# ---------------------------------------------------------------------------
from cli.commands.test_all import run_test_all
app.command("test:all")(run_test_all)


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
# krystal post <target>
# ---------------------------------------------------------------------------
from cli.commands.post import run_post

@app.command("post")
def cmd_post(target: str = typer.Argument(..., help="Ruta del Widget, Mod o Theme a empaquetar en .kzip")):
    """
    📦  Package and publish a specific module to the KrystalOS Registry (.kzip)
    """
    run_post(target)


# ---------------------------------------------------------------------------
# krystal make (Command Group)
# ---------------------------------------------------------------------------
from cli.commands.theme_scaffolder import theme_app
app.add_typer(theme_app, name="make") 
# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
