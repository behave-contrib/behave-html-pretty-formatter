#!/usr/bin/env python3
"""
Main file where the python code is located for execution via behave.
"""

from behave import step


@step('Dummy pass')
def dummy_pass(context):  # pylint: disable=unused-argument
    """
    Dummy step to always PASS.

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    assert True, "This step always passes."


@step('Dummy fail')
def dummy_fail(context):  # pylint: disable=unused-argument
    """
    Dummy step to always FAIL.

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    error_message = "This test always fails."
    raise AssertionError(error_message)


@step('Dummy skip')
def dummy_skip(context):  # pylint: disable=unused-argument
    """
    Dummy step to always SKIP.

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    context.scenario.skip("Scenario Skipped.")


@step('Commentary')
def commentary_step(context) -> None:
    """
    Commentary step for usage in behave feature files - html-pretty only.

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    # Defined only for html-pretty formatter.
    # This will return an instance of PrettyHTMLFormatter.
    formatter_instance = getattr(context, "html_formatter", None)
    if formatter_instance is not None and formatter_instance.name == "html-pretty":
        # Get the correct step to override.
        scenario = formatter_instance.current_scenario
        # Current scenario is never none, as this step is being executed.
        scenario_step = scenario.current_step

        # Override the step, this will prevent the decorator to be generated and only
        # the text will show.
        scenario_step.set_commentary(True)


@step('Table Example')
def table_example(context) -> None:
    """
    Table Example

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    for row in context.table:
        pass

        #field = row["Field"]
        #data = row["Data"]

        # do_stuff(field, data)


@step('Text Example')
def text_example(context) -> None:
    """
    Text Example

    :param context: Holds contextual information during the running of tests.
    :type context: <behave.runner.Context>
    """

    # do_stuff(context.text)

