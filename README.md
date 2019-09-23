# Html formatter for Behave

To use it with behave create behave.ini file in project folder (or in home) with
following content:

    # -- FILE: behave.ini
    # Define ALIAS for HtmlFormatter.
    [behave.formatters]
    html = behave_html_formatter:HTMLFormatter

and then use it by running behave with `-f html` parameter.

You can find information about behave and user-defined formatters
in behave's documentation: <https://behave.readthedocs.io/en/latest/>
