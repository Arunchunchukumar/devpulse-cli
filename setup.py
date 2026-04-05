from setuptools import setup, find_packages

setup(
    name="devpulse-cli",
    version="0.3.0",
    author="Arun Kumar",
    author_email="arunch.pluto@gmail.com",
    description="CLI tool for monitoring GitHub PR activity, CI status, and team velocity",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Arunchunchukumar/devpulse-cli",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1.7",
        "rich>=13.7.0",
        "httpx>=0.26.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-asyncio>=0.23.0", "ruff>=0.1.0", "mypy>=1.8.0"],
    },
    entry_points={
        "console_scripts": ["devpulse=devpulse.cli:main"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
