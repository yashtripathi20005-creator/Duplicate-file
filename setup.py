# filename: setup.py

"""
Setup script for Duplicate File Finder
"""

from setuptools import setup, find_packages

setup(
    name="duplicate-finder",
    version="1.0.0",
    description="Find and manage duplicate files in a directory tree",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/duplicate-finder",
    packages=find_packages(),
    py_modules=["duplicate_finder"],
    entry_points={
        "console_scripts": [
            "duplicate-finder=duplicate_finder:main",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
)
