# HTML formatter for Behave

To use it with behave create `behave.ini` file in project folder (or in home) with
following content:

```ini
# -- FILE: behave.ini
# Define ALIAS for HtmlFormatter.
[behave.formatters]
html = behave_html_formatter:HTMLFormatter
```

and then use it by running behave with `-f`/`--format` parameter, e.g.

```console
behave -f help
behave -f html
behave -f html -o behave-report.html
```

You can find information about behave and user-defined formatters in the
[behave docs](https://behave.readthedocs.io/en/latest/formatters.html).

## Contributing

You want to help with improving this software? Please create an issue in
our open bug tracker, or open a pull request directly.

We use [tox](https://pypi.org/project/tox/) for running linting and tests,
e.g.

```console
tox
tox -l
tox -e flake8,behave
```

For code formatting we use [black](https://pypi.org/project/black/), which
you can run using our Tox setup, e.g.

```console
tox -e black
```

If you need to change CSS or JavaScript code: First edit the regular files,
then generate the minified versions like so:

```console
tox -e minify
```
