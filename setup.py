"""Setup script for Novel Writing Agent package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="novel-agent",
    version="1.0.0",
    description="AI-powered novel writing assistant using LangChain",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Novel Agent Team",
    author_email="",
    url="",
    packages=find_packages(include=["novel_agent", "novel_agent.*"]),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "novel-agent=novel_agent.cli:main",
        ],
    },
)
