"""
Packaging setup for behave-html-formatter.
"""
from setuptools import find_packages, setup


def read_file(filename):
    """Return the content of a file."""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="behave-html-formatter",
    version="0.9.9",
    author="Petr Schindler",
    author_email="pschindl@redhat.com",
    description="HTML formatter for Behave",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/behave-contrib/behave-html-formatter",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: BDD",
    ],
    include_package_data=True,
    packages=find_packages(exclude="tests"),
    python_requires=">=3.6",
    install_requires=["behave"],
)
