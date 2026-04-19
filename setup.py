"""Package setup for vaultpull."""
from setuptools import setup, find_packages

setup(
    name="vaultpull",
    version="0.1.0",
    description="CLI tool to sync secrets from HashiCorp Vault into local .env files.",
    author="vaultpull contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "click>=8.0",
        "hvac>=1.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "vaultpull=vaultpull.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
