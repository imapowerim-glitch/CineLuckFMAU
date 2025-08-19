#!/usr/bin/env python3
"""
CineLuck - Professional Raspberry Pi Video Camera
Setup script for installation and packaging
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cineluck",
    version="1.0.0",
    author="CineLuck Development Team",
    author_email="dev@cineluck.com",
    description="Professional Raspberry Pi 5 video camera using Picamera2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/imapowerim-glitch/CineLuckFMAU",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video :: Capture",
        "Topic :: Multimedia :: Video :: Display",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cineluck=cineluck.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cineluck": [
            "ui/assets/*",
            "config/defaults/*",
        ],
    },
    data_files=[
        ("share/applications", ["scripts/cineluck.desktop"]),
        ("share/pixmaps", ["assets/cineluck-icon.png"]),
    ],
)