from setuptools import setup, find_packages

setup(
    name="krystal-commander",
    version="0.1.0",
    description="KrystalOS CLI — Phase 1: Foundation",
    author="TzitzuStudio",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "typer[all]>=0.12.0",
        "rich>=13.7.0",
        "psutil>=5.9.0",
        "pydantic>=2.6.0",
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
