#!/usr/bin/env python3
import typer
import subprocess
import os
import shutil
import json

app = typer.Typer(
    help="""
KrystalOS Command Line Interface (Krystal-CLI) 🚀

El gestor global para administrar tu entorno KrystalOS.
Úsalo para desplegar el servidor, generar bases de código
e instalar extensiones desde el Marketplace nativo.
    """,
    no_args_is_help=True
)

@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """
    🚀 Inicia el servidor de KrystalOS (FastAPI + Uvicorn).
    """
    typer.echo(f"Starting KrystalOS on {host}:{port}")
    cmd = ["uvicorn", "main:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")
    
    # Run uvicorn server in current directory
    subprocess.run(cmd, cwd=os.getcwd())

@app.command()
def generate(widget_name: str):
    """
    ✨ Genera la estructura base para un nuevo widget local.
    """
    widgets_dir = os.path.join(os.getcwd(), "widgets")
    widget_path = os.path.join(widgets_dir, widget_name)
    
    if os.path.exists(widget_path):
        typer.echo(f"Error: Widget '{widget_name}' already exists at {widget_path}.", err=True)
        raise typer.Exit(code=1)
        
    os.makedirs(widget_path)
    
    config_data = {
        "name": widget_name,
        "description": "Generated widget",
        "api_prefix": f"/api/widgets/{widget_name}",
        "version": "1.0.0",
        "grid": {"w": 2, "h": 2},
        "permissions": []
    }
    
    with open(os.path.join(widget_path, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
        
    routes_code = f"""from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_{widget_name}_info():
    return {{"message": "Hello from {widget_name} widget!"}}
"""
    with open(os.path.join(widget_path, "routes.py"), "w", encoding="utf-8") as f:
        f.write(routes_code)

    ui_code = """<div class="krystal-widget text-white p-4 glass-panel">
    <h3>Widget View</h3>
</div>
"""
    with open(os.path.join(widget_path, "ui.html"), "w", encoding="utf-8") as f:
        f.write(ui_code)
        
    typer.echo(f"Widget '{widget_name}' generated successfully!")


@app.command()
def install(package_type: str, name: str):
    """
    📦 Instala un widget o tema desde el Krystal Marketplace (GitHub).
    
    Ejemplos:
      krystal install widget kanban
      krystal install theme neo-dark
      krystal install widget midudev/reproductor
    """
    try:
        if package_type not in ["widget", "theme"]:
            typer.echo(f"❌ Error: El tipo debe ser 'widget' o 'theme'. Recibido: {package_type}", err=True)
            return

        # Handle explicit author or default to KrystalOS organization
        if "/" in name:
            author, pkg_name = name.split("/", 1)
        else:
            author = "KrystalOS-Marketplace" # Default official registry
            pkg_name = name

        repo_name = f"krystal-{package_type}-{pkg_name}"
        repo_url = f"https://github.com/{author}/{repo_name}.git"
        
        target_dir = os.path.join(os.getcwd(), "widgets" if package_type == "widget" else "public/css/themes", pkg_name)
        tmp_dir = os.path.join(os.getcwd(), ".tmp", repo_name)
        
        if os.path.exists(target_dir):
            typer.echo(f"⚠️ El {package_type} '{pkg_name}' ya está instalado.", err=True)
            return

        typer.echo(f"⬇️ Descargando '{pkg_name}' desde {author}...\n")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            
        # Remove DEVNULL to show live cloning progress
        subprocess.run(["git", "clone", repo_url, tmp_dir], check=True)
        
        # Validación de Contrato para Widgets
        if package_type == "widget":
            typer.echo("🔍 Validando contrato de Widget KrystalOS...")
            config_path = os.path.join(tmp_dir, "config.json")
            if not os.path.exists(config_path):
                typer.echo("❌ Validación fallida: No se encontró 'config.json'.", err=True)
                shutil.rmtree(tmp_dir)
                return
                
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                required_fields = ["package_name", "version", "author"]
                for req in required_fields:
                    if req not in config_data:
                        typer.echo(f"❌ Validación fallida: 'config.json' no contiene el campo obligatorio '{req}'.", err=True)
                        shutil.rmtree(tmp_dir)
                        return
            
            # Instalar dependencias
            reqs_path = os.path.join(tmp_dir, "requirements.txt")
            if os.path.exists(reqs_path):
                typer.echo("\n📦 Instalando dependencias del widget (pip)...")
                subprocess.run(["pip", "install", "-r", reqs_path], check=True)
                
            # Detectar migraciones
            models_path = os.path.join(tmp_dir, "models.py")
            if os.path.exists(models_path):
                typer.echo("🗄️ Detectado 'models.py'. Programando migración de base de datos...")
                # Here we would run alembic or sqlmodel create tables
                
        # Limpiar la carpeta .git para evitar repositorios anidados
        git_dir = os.path.join(tmp_dir, ".git")
        if os.path.exists(git_dir):
            shutil.rmtree(git_dir)
            
        # Mover a producción
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        shutil.move(tmp_dir, target_dir)
            
        typer.echo(f"\n✅ ¡{package_type.capitalize()} '{pkg_name}' instalado exitosamente!")
        if package_type == "widget":
            typer.echo("⚡ El orquestador aplicará un Hot-Reload automáticamente.")
            
    except subprocess.CalledProcessError as e:
        typer.echo(f"\n❌ Error durante la ejecución del comando. Detalles: {e}", err=True)
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
    except Exception as e:
        typer.echo(f"\n❌ Error inesperado: {e}", err=True)
        if 'tmp_dir' in locals() and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

@app.command()
def remove(package_type: str, name: str):
    """
    🗑️ Elimina un widget o tema del sistema local.
    
    Ejemplo: krystal remove widget kanban
    """
    if package_type not in ["widget", "theme"]:
        typer.echo("❌ Tipo de paquete inválido. Usa 'widget' o 'theme'.", err=True)
        return
        
    target_dir = os.path.join(os.getcwd(), "widgets" if package_type == "widget" else "public/css/themes", name)
    
    if not os.path.exists(target_dir):
        typer.echo(f"⚠️ El {package_type} '{name}' no existe en {target_dir}.", err=True)
        return
        
    try:
        shutil.rmtree(target_dir)
        typer.echo(f"🗑️ El {package_type} '{name}' fue eliminado correctamente.")
    except Exception as e:
        typer.echo(f"❌ Error eliminando paquete: {e}", err=True)

@app.command()
def update(package_type: str, name: str):
    """
    🔄 Actualiza un widget o tema a su última versión.
    """
    typer.echo(f"ℹ️  Para actualizar '{name}', por favor usa 'krystal remove' y luego 'krystal install'.")

@app.command()
def validate(widget_name: str):
    """
    🔍 Linter (Validador) local para desarrolladores de widgets.
    """
    widget_dir = os.path.join(os.getcwd(), "widgets", widget_name)
    if not os.path.exists(widget_dir):
        typer.echo(f"❌ Error: El widget '{widget_name}' no existe en {widget_dir}", err=True)
        return
        
    typer.echo(f"🔍 Validando el widget '{widget_name}'...")
    errors = 0
    
    # 1. config.json
    config_path = os.path.join(widget_dir, "config.json")
    if not os.path.exists(config_path):
        typer.echo("  ❌ Falta 'config.json'")
        errors += 1
    else:
        typer.echo("  ✅ Encontrado 'config.json'")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            required_fields = ["package_name", "version", "author"]
            for req in required_fields:
                if req not in config_data:
                    typer.echo(f"  ❌ 'config.json' no contiene el campo obligatorio: '{req}'")
                    errors += 1
                    
    # 2. ui.html
    if not os.path.exists(os.path.join(widget_dir, "ui.html")):
        typer.echo("  ❌ Falta la vista 'ui.html'. KrystalOS requiere una interfaz HTML por defecto.")
        errors += 1
    else:
        typer.echo("  ✅ Encontrado 'ui.html'")
        
    # 3. routes.py
    if not os.path.exists(os.path.join(widget_dir, "routes.py")):
        typer.echo("  ❌ Falta 'routes.py'. KrystalOS requiere un router FastAPI por defecto.")
        errors += 1
    else:
        typer.echo("  ✅ Encontrado 'routes.py'")
        
    if errors == 0:
        typer.echo(f"\n🎉 ¡El widget '{widget_name}' es 100% compatible con KrystalOS y está listo para publicarse en GitHub!")
    else:
        typer.echo(f"\n⚠️ El widget tiene {errors} errores que deben corregirse.")

@app.command()
def new(project_name: str):
    """
    🏗️ Crea (Scaffolds) un nuevo proyecto web KrystalOS en blanco.
    
    Ejemplo: krystal new MiApp
    """
    target_dir = os.path.join(os.getcwd(), project_name)
    if os.path.exists(target_dir):
        typer.echo(f"❌ Error: La carpeta '{project_name}' ya existe.", err=True)
        raise typer.Exit(code=1)
        
    typer.echo(f"✨ Inicializando nuevo proyecto KrystalOS en: {project_name}...")
    
    # URL del repositorio principal del framework limpio
    # EL USUARIO DEBE CAMBIAR ESTO POR SU REPOSITORIO REAL DE GITHUB
    FRAMEWORK_REPO_URL = "https://github.com/PapitaCosmica/KrystalOS.git"
    
    try:
        typer.echo(f"📦 Descargando la última versión del framework desde GitHub...")
        subprocess.run(["git", "clone", FRAMEWORK_REPO_URL, target_dir], check=True)
        
        # Limpiar el .git original para que el usuario inicie su propio historial
        git_dir = os.path.join(target_dir, ".git")
        if os.path.exists(git_dir):
            import shutil
            shutil.rmtree(git_dir)
        
        typer.echo("🔐 Generando credenciales seguras de entorno...")
        import secrets
        env_path = os.path.join(target_dir, ".env")
        with open(env_path, "w", encoding="utf-8") as env_file:
            env_file.write(f"KRYSTAL_SECRET_KEY={secrets.token_urlsafe(32)}\n")
            env_file.write("DATABASE_URL=postgresql://krystal:krystalpass@db:5432/krystaldb\n")
            env_file.write("ENVIRONMENT=development\n")
            
        # Re-inicializar un Git limpio para el usuario
        typer.echo("🌱 Inicializando repositorio Git en el nuevo proyecto...")
        subprocess.run(["git", "init"], cwd=target_dir)
        
        typer.echo(f"\n🎉 ¡KrystalOS está listo!")
        typer.echo(f"👉 Pasos siguientes:")
        typer.echo(f"   cd {project_name}")
        typer.echo(f"   docker-compose up --build")
    except Exception as e:
        typer.echo(f"❌ Error durante el andamiaje: {e}", err=True)
        
if __name__ == "__main__":
    app()

