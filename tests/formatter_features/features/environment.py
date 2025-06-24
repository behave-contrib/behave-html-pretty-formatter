#!/usr/bin/env python3

"""
This file provides setup for machine environment for our testing pipeline.
"""

# pylint: disable=broad-exception-caught
# ruff: noqa: BLE001

import sys
import traceback

from qecore.sandbox import TestSandbox


def before_all(context) -> None:
    """
    This function will be run once in every 'behave' command called.
    """

    try:

        context.sandbox = TestSandbox("dummy", context=context)

        # Adds only noise to this example, turning it off.
        context.sandbox.status_report = False
        context.sandbox.change_title = False

        context.dummy = context.sandbox.get_application(
            name="dummy", desktop_file_exists=False,
        )

        for formatter in context._runner.formatters:
            if formatter.name == "html-pretty":
                context.html_formatter = formatter

    except Exception as error:
        print(f"Environment error: before_all: {error}")
        traceback.print_exc(file=sys.stdout)

        # Save the traceback so that we can use it later when we have html report.
        context.failed_setup = traceback.format_exc()


def before_scenario(context, scenario) -> None:
    """
    This function will be run before every scenario in 'behave' command called.
    """

    try:
        context.sandbox.before_scenario(context, scenario)

        if "dummy_scenario_pass_pseudo_steps" in scenario.effective_tags:
            context.html_formatter.pseudo_steps = True

            error_found = "An error has not occurred."
            if error_found == "An error has occurred.":
                context.embed("text", str(error_found), "Error Message")
                context.html_formatter.before_scenario_finish("failed")
                raise RuntimeError(error_found)

            context.html_formatter.before_scenario_finish("passed")

    except Exception as error:
        print(f"Environment error: before_scenario: {error}")
        traceback.print_exc(file=sys.stdout)

        # Attach failed setup from Before Scenario to our html-pretty report.
        embed_caption = "Failed cleanup in Before Scenario"
        context.embed("text", traceback.format_exc(), embed_caption)

        # Recommended to correctly place the embed to the Before Scenario.
        sys.exit(1)


def after_scenario(context, scenario) -> None:
    """
    This function will be run after every scenario in 'behave' command called.
    """

    try:
        context.sandbox.after_scenario(context, scenario)

        if "dummy_scenario_pass_pseudo_steps" in scenario.effective_tags:

            error_found = "An error has not occurred."
            if error_found == "An error has occurred":
                context.embed("text", str(error_found), "Error Message")
                context.html_formatter.after_scenario_finish("failed")
                raise RuntimeError(error_found)

            context.html_formatter.after_scenario_finish("passed")
            context.html_formatter.pseudo_steps = False


    except Exception as error:
        print(f"Environment error: after_scenario: {error}")
        traceback.print_exc(file=sys.stdout)

        # Attach failed setup from After Scenario to our html-pretty report.
        embed_caption = "Failed cleanup in After Scenario"
        context.embed("text", traceback.format_exc(), embed_caption)

