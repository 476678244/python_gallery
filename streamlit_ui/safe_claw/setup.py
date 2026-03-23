"""Setup script for SafeClaw"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="safe-claw",
    version="0.1.0",
    author="SafeClaw Team",
    author_email="team@safeclaw.ai",
    description="The Real AI Safety Assistant - SafeClaw TRASA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/safeclaw/safe-claw",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.5.0",
            "mkdocstrings>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "safe-claw=streamlit_ui.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "streamlit_ui": ["styles/*.css", "pages/*.py"],
    },
)
