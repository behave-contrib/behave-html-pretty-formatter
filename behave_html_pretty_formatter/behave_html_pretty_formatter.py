# Inspired by https://github.com/Hargne/jest-html-reporter

from __future__ import absolute_import
import sys
import traceback
from curses import raw
from posixpath import abspath
from pathlib import Path
from datetime import datetime

import dominate
from dominate.tags import *
from dominate.util import raw

from behave.formatter.base import Formatter
from behave.model_core import Status
from behave.runner_util import make_undefined_step_snippets


DEFAULT_CAPTION_FOR_MIME_TYPE = {
    "video/webm": "Video",
    "image/png": "Screenshot",
    "text": "Data",
    "link": "Link",
}


class Feature:
    def __init__(self, feature):
        self._feature = feature
        self.name = feature.name
        self.tags = feature.tags
        self.keyword = feature.keyword
        self.description = feature.description
        self.location = feature.location
        self.status = None

        self.scenarios = []

    def add_scenario(self, scenario):
        _scenario = Scenario(scenario, self)
        self.scenarios.append(_scenario)
        return _scenario


class Scenario:
    def __init__(self, scenario, feature):
        self._scenario = scenario
        self.feature = feature
        self.keyword = scenario.keyword
        self.name = scenario.name
        self.description = scenario.description
        self.tags = scenario.effective_tags
        self.location = scenario.location
        self.steps = {}
        self.status = None
        self.duration = 0.0
        self.result_id = 0
        self.steps = []

    def add_step(self, step):
        _step = Step(step, self)
        self.steps.append(_step)
        return _step

    def add_result(self, result):
        step = self.steps[self.result_id]
        step.add_result(result)
        if self.result_id == len(self.steps) or\
                result.status == Status.passed or\
                result.status == Status.failed or\
                result.status == Status.undefined:
            self.status = result.status.name
            self.duration = self._scenario.duration
        # So after_scenario embeds are not in the next step.
        if result.status != Status.failed:
            self.result_id += 1
        return step

    def embed(self, embed_data):
        if len(self.steps) <= self.result_id:
            step = self.steps[-1]
        else:
            step = self.steps[self.result_id]
        step.embed(embed_data)


class Step:
    def __init__(self, step, scenario):
        self.status = None
        self.duration = 0.0
        self.scenario = scenario
        self.keyword = step.keyword
        self.step_type = step.step_type
        self.name = step.name
        self.text = step.text
        self.table = step.table
        self.location = f"{abspath(step.location.filename)}:{step.location.line}"
        self.embeds = []

    def add_result(self, result):
        self.status = result.status.name
        self.duration = result.duration

        # If the step has error message and step failed, set the error message to the data structure.
        if result.error_message and result.status == Status.failed:
            self.error_message = result.error_message
            self.embed(Embed(mime_type="text", data=self.error_message, caption="Error Message"))

        # If the step is undefined use the behave function to provide information and save it to data structure.
        if result.status == Status.undefined:
            undefined_step_message = u"\nYou can implement step definitions for undefined steps with "
            undefined_step_message += u"these snippets:\n\n"
            undefined_step_message += u"\n".join(make_undefined_step_snippets(undefined_steps=[result]))

            self.error_message = undefined_step_message
            self.embed(Embed(mime_type="text", data=self.error_message, caption="Error Message"))

    def embed(self, embed_data):
        self.embeds.append(embed_data)


class Embed:
    def __init__(self, mime_type, data, caption=None, fail_only=False):
        self.mime_type = mime_type
        self.data = data
        self.caption = caption
        self.fail_only = fail_only


# Heavily based on behave.formatter.json:JSONFormatter
# Since we need some form of structure from where we will pull all data upon close.
# Modifications based on our needs and experimentation.
class PrettyHTMLFormatter(Formatter):
    name = "html-pretty"
    description = "Pretty HTML formatter"

    def __init__(self, stream, config):
        super(PrettyHTMLFormatter, self).__init__(stream, config)

        self.features = []

        self.high_contrast_button = False
        self.embed_number = 0
        self.table_number = 0

        self.suite_start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Theory of what this will do:
        # This will return a stream given in behave call -o report.html.
        self.stream = self.open()


    def feature(self, feature):
        print("DEBUG, executing feature")
        self.current_feature = Feature(feature)
        self.features.append(self.current_feature)


    def scenario(self, scenario):
        print("DEBUG, executing scenario")
        self.current_scenario = self.current_feature.add_scenario(scenario)


    def step(self, step):
        print("DEBUG, executing step")
        self.current_scenario.add_step(step)


    def result(self, step):
        print("DEBUG, executing result")
        self.current_scenario.add_result(step)

    def reset(self, reset):
        #print("debug, running reset function - currently unknown if needed")
        pass

    def uri(self, uri):
        #print("debug, running uri function - currently unknown if needed")
        pass

    def match(self, match):
        #print(f"debug, running match function - currently unknown if needed: {match}")
        #print(f"match location {match.location}")
        pass

    def background(self, background):
        #print("debug, running background function - currently unknown if needed")
        pass


    # Making bold text in between quotes.
    def make_bold_text(self, given_string):
        quote_count = given_string.count("\"")

        # Save string to iterate over.
        the_rest = given_string
        for _ in range(int(quote_count/2)):
            first_part, bold_text, the_rest = the_rest.split("\"", 2)

            span(first_part)
            span(" \"")
            b(bold_text)
            span("\" ")

        span(the_rest)


    # Used to generate a steps.
    def generate_step(self,
                      step_result="None",
                      step_decorator="None",
                      step_duration="None",
                      step_link_label="None",
                      step_link_location="None"):

        with div(cls=f"step-capsule step-capsule-{step_result}"):

            with div(cls="step-status-decorator-duration-capsule"):
                with div(cls="step-status"):

                    # Behave defined status strings are "passed" "failed" "undefined" "skipped".
                    # Modify these values for high contrast usage.
                    high_contrast_status = {
                        "passed": "PASS",
                        "failed": "FAIL",
                        "undefined": "SKIP",
                        "skipped": "SKIP"
                    }
                    # Step status for high contrast - "PASS" "FAIL" "SKIP".
                    span(high_contrast_status[step_result])

                with div(cls="step-decorator"):
                    # Step decorator.
                    self.make_bold_text(step_decorator)

                with div(cls="step-duration"):
                    short_duration = "{:.2f}s".format(step_duration)
                    # Step duration.
                    span(f"({short_duration})")

            with div(cls="link"):
                with a(href=step_link_location):
                    # Step link.
                    span(step_link_label)


    def data_embeding_function(self, mime_type, data, caption=None, last=True, scenario_result="passed"):
        self.embed_number += 1

        # If caption is user defined.
        if caption is not None:
            use_caption = caption
        # If caption is not defined try to use default one for specific mime type.
        elif mime_type in DEFAULT_CAPTION_FOR_MIME_TYPE.keys():
            use_caption = DEFAULT_CAPTION_FOR_MIME_TYPE[mime_type]
        # No caption and no default caption for given mime type.
        else:
            use_caption = "uknown-mime-type"
            data = "data removed"

        # Serves for css embed purpose for the dotted line after the last embed.
        dashed_line = f"messages-{scenario_result}-dashed" if last else ""

        with div(cls=f"messages {dashed_line}"):
            with div(cls="embed-capsule"):

                # Embed Caption.
                with div(cls="embed_button"):
                    with div(cls="link"):
                        # Label to be shown.
                        with a(href="#/", onclick=f"collapsible_toggle('embed_{self.embed_number}')"):
                            span(use_caption)

                # Actual Embed.
                if "video/webm" in mime_type:
                    with pre(cls="embed_content"):
                        with video(id=f"embed_{self.embed_number}", style="display: none", width="1024", controls=""):
                            source(src=f"data:{mime_type};base64,{data}    ", type=mime_type)

                if "image/png" in mime_type:
                    with pre(cls="embed_content", id=f"embed_{self.embed_number}", style="display: none"):
                        img(src=f"data:{mime_type};base64,{data}    ")

                if "text" in mime_type:
                    with pre(cls="embed_content", id=f"embed_{self.embed_number}", style="display: none"):
                        span(data)

                if "link" in mime_type:
                    with pre(cls="embed_content", id=f"embed_{self.embed_number}", style="display: none"):
                        with a(href=data):
                            span(data)


    def embedding(self, mime_type, data, caption=None, fail_only=False):
        # Find correct scenario.
        embed_data = Embed(mime_type, data, caption, fail_only)
        self.current_scenario.embed(embed_data)
        return embed_data


    def generate_table(self, given_table):
        table_headings = given_table.headings
        table_rows = given_table.rows

        # Generate Table.
        with table():

            # Make a heading.
            with thead(onclick=f"collapsible_toggle('table_{self.table_number}')"):
                line = tr()
                for heading in table_headings:
                    line += th(heading)

            # Make the body.
            with tbody(id=f"table_{self.table_number}"):
                for row in table_rows:
                    with tr() as line:
                        for cell in row:
                            line += td(cell)

        self.table_number += 1


    def close(self):
        # Try block to be removed - debugging purposes only.
        try:
            # Generate everything.
            self.document = dominate.document(title="Test Suite Reporter", pretty_flags=False)

            # Iterate over the data and generate the page.
            with self.document.head:
                # Load and insert css theme.
                with open(Path(__file__).parent / "theme.css", "r", encoding="utf-8") as _css_file:
                    css_theme = _css_file.read()
                with style(rel="stylesheet"):
                    raw(css_theme)

                # Load and insert javascript - important for embed toggles and high contrast switch.
                with open(Path(__file__).parent / "script.js", "r", encoding="utf-8") as _script_file:
                    js_script = _script_file.read()
                with script(type="text/javascript"):
                    raw(js_script)


                ########## FEATURE FILE ITERATION ##########
                # Base structure for iterating over Features.
                for feature_id, feature in enumerate(self.features):
                    # Feature Panel
                    with div(cls="feature-panel"):

                        # Generate content of the panel.
                        if not self.high_contrast_button:
                            # Making sure there is a functioning button.
                            with a(onclick=f"toggle_contrast('embed')"):
                                # Creating the actual text content which is clickable.
                                span(f"Feature: {feature.name} [High Contrast toggle]")
                                # Set the flag to be sure there is not another one created.
                                self.high_contrast_button = True

                        # On another feature do not generate the button.
                        else:
                            span(f"Feature: {feature.name}")

                        # Suite started information.
                        with div(cls="feature-timestamp"):
                            span("Started: " + self.suite_start_time)

                    # Feature data container.
                    with div(cls="feature-container"):

                        ########## SCENARIOS ITERATION ##########
                        # Base structure for iterating over Scenarios in Features.
                        for scenario_id, scenario in enumerate(feature.scenarios):
                            # Scenario container.
                            with div(cls=f"scenario-capsule scenario-capsule-{scenario.status}"):

                                # TODO use the effective tags here, which will pull it from the feature also.
                                for tag in scenario.tags:
                                    with div(cls="scenario-tags"):
                                        with div(cls="link"):
                                            # TODO LINK
                                            with a(href="#/"):
                                                span("@"+tag)

                                # Simple container for name + duration
                                with div(cls="scenario-info"):

                                    with div(cls="scenario-name"):
                                        span(f"Scenario: {scenario.name}")

                                    with div(cls="scenario-duration"):
                                        span(f"Scenario duration: {scenario.duration:.2f}s")

                                ########## STEP ITERATION ##########
                                # Base structure for iterating over Steps in Scenarios.
                                for step_id, step in enumerate(scenario.steps):

                                    step_decorator = step.keyword + " " + step.name
                                    step_duration = step.duration
                                    step_link = step.location
                                    step_result = step.status

                                    # Treat None step_result as skipped.
                                    step_result = step_result if step_result else "skipped"

                                    # Generate the step.
                                    self.generate_step(
                                        step_result=step_result,
                                        step_decorator=step_decorator,
                                        step_duration=step_duration,
                                        step_link_label=step_link,
                                        step_link_location="#" # TODO dynamic
                                    )

                                    # Generate table for a step if present.
                                    if step.table is not None:
                                        self.generate_table(step.table)

                                    if step.text is not None:
                                        self.generate_text(step.text)

                                    # Generate all embeds that are in the data structure.
                                    last_embed_id = len(step.embeds) - 1
                                    for embed_id, embed_data in enumerate(step.embeds):
                                        if embed_data.fail_only and step_result != "failed":
                                            continue
                                        self.data_embeding_function(
                                            mime_type=embed_data.mime_type,
                                            data=embed_data.data,
                                            caption=embed_data.caption,
                                            last=embed_id == last_embed_id,
                                            scenario_result=step_result
                                        )

            # Write everything to the stream which should corelate to the -o <file> behave option.
            self.stream.write(self.document.render())

        except Exception:
            traceback.print_exc(file=sys.stdout)
