"""
Packaging setup for behave-html-pretty-formatter.
"""
import setuptools


def read_file(filename):
    """Return the content of a file."""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


setuptools.setup(
    name="behave-html-pretty-formatter",
    version="1.6",
    author="Michal Odehnal",
    author_email="modehnal@redhat.com",
    description="""
Pretty HTML Formatter for Behave

Authors:
Michal Odehnal <modehnal@redhat.com>,
Filip Pokryvka <fpokryvk@redhat.com>

Github contributors:
@bittner
@lu-maca
""",
    url="https://github.com/behave-contrib/behave-html-pretty-formatter",
    packages=setuptools.find_packages(),
    install_requires=[
        "behave",
        "dominate",
        "markdown",
    ],
    include_package_data=True,
    python_requires=">=3.6",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: BDD",
    ],
)
