from setuptools import setup, find_packages

setup(
    name="krystal-commander",
    version="0.2.0",
    description="KrystalOS CLI — Phase 2: The Orchestrator",
    author="TzitzuStudio",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        # Phase 1
        "typer[all]>=0.12.0",
        "rich>=13.7.0",
        "psutil>=5.9.0",
        "pydantic>=2.6.0",
        # Phase 2
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.29.0",
        "sqlmodel>=0.0.16",
        "httpx>=0.27.0",
        "aiofiles>=23.2.1",
        "jinja2>=3.1.3",
        "psycopg2-binary>=2.9.9",
    ],
    entry_points={
        "console_scripts": [
            "krystal=cli.main:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
