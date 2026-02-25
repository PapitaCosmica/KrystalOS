from setuptools import setup, find_packages

setup(
    name="krystalos-cli",
    version="1.0.0",
    description="KrystalOS Global Framework CLI",
    author="Krystal",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0"
    ],
    entry_points={
        "console_scripts": [
            "krystal=bin.krystal:app",
        ],
    },
)
