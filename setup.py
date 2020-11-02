import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="behave-html-formatter",
    version="0.9.6",
    author="Petr Schindler",
    author_email="pschindl@redhat.com",
    description="HTML formatter for Behave",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/schidlo/behave-html-formatter",
    packages=setuptools.find_packages(),
    install_requires=['behave'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
