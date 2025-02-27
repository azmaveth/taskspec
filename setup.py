"""
Setup script for taskspec package.
"""

from setuptools import setup, find_packages

setup(
    name="taskspec",
    version="0.1.0",
    description="A Python CLI tool that uses LLMs to analyze tasks and generate specifications",
    author="",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.6.0",
        "litellm>=1.16.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.0",
        "statistics>=1.0.3.5",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "mutmut>=3.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "taskspec=taskspec.main:app",
            "ts=taskspec.main:app",
        ],
    },
    scripts=["bin/ts"],
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)