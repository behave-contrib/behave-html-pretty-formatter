# Inspired by https://github.com/Hargne/jest-html-reporter

from __future__ import absolute_import
import os
import sys
import traceback
import base64
import time
from pathlib import Path
from datetime import datetime

import dominate
from dominate.tags import (
    div,
    span,
    a,
    b,
    table,
    tbody,
    thead,
    tr,
    th,
    td,
    pre,
    video,
    source,
    script,
    img,
    style,
)
from dominate.util import raw

from behave.formatter.base import Formatter
from behave.model_core import Status
from behave.runner_util import make_undefined_step_snippets


# TODO
# Timestamp next to the human-readable time.


DEFAULT_CAPTION_FOR_MIME_TYPE = {
    "video/webm": "Video",
    "image/png": "Screenshot",
    "text": "Data",
    "link": "Link",
}


class Feature:
    def __init__(self, feature):
        self.name = feature.name
        self.description = feature.description
        self.location = feature.location
        self.status = None

        self.scenarios = []
        self.to_embed = []
        self.scenario_begin_timestamp = time.time()
        self.before_scenario_duration = 0.0
        self.before_scenario_status = "skipped"

    def add_scenario(self, scenario, pseudo_steps=False):
        _scenario = Scenario(scenario, self, pseudo_steps)
        for embed_data in self.to_embed:
            _scenario.embed(embed_data)
        self.to_embed = []

        if pseudo_steps:
            _step = _scenario.before_scenario_step
            _step.duration = self.before_scenario_duration
            _step.status = self.before_scenario_status

        self.scenarios.append(_scenario)
        return _scenario

    def embed(self, embed_data):
        if not self.scenarios:
            self.to_embed.append(embed_data)
        else:
            self.scenarios[-1].embed(embed_data)

    def before_scenario_finish(self, status):
        self.before_scenario_duration = time.time() - self.scenario_begin_timestamp
        self.before_scenario_status = status

    def after_scenario_finish(self, status):
        _scenario = self.scenarios[-1]
        _step = _scenario.after_scenario_step
        if _step is not None:
            _step.duration = time.time() - _scenario.steps_finished_timestamp
            _step.status = status
            self.scenario_begin_timestamp = time.time()


class Scenario:
    def __init__(self, scenario, feature, pseudo_steps=False):
        self._scenario = scenario
        self.feature = feature
        self.name = scenario.name
        self.description = scenario.description
        self.pseudo_steps = []
        if pseudo_steps:
            self.pseudo_steps = [
                Step(when, "scenario", None, None, self) for when in ("Before", "After")
            ]

        # We need another information about a tag, to recognize if it should act as a link or span.
        self.tags = [Tag(tag) for tag in scenario.effective_tags]

        self.location = scenario.location
        self.status = None
        self.duration = 0.0
        self.match_id = -1
        self.steps_finished = False
        self.steps_finished_timestamp = None
        self.steps = []
        self.to_embed = []

        self.saved_matched_filename = None
        self.saved_matched_line = None

    @property
    def before_scenario_step(self):
        if self.pseudo_steps:
            return self.pseudo_steps[0]

        return None

    @property
    def after_scenario_step(self):
        if self.pseudo_steps:
            return self.pseudo_steps[1]

        return None

    @property
    def current_step(self):
        _step = None
        if self.match_id < 0:
            if self.pseudo_steps:
                _step = self.pseudo_steps[0]
            elif self.steps:
                _step = self.steps[0]

        if self.steps_finished:
            if self.pseudo_steps:
                _step = self.pseudo_steps[1]

        if _step is None and self.steps:
            _step = self.steps[self.match_id]

        return _step

    @property
    def is_last_step(self):
        return self.match_id + 1 >= len(self.steps)

    def add_step(self, keyword, name, text=None, table=None):
        _step = Step(keyword, name, text, table, self)
        self.steps.append(_step)
        for embed_data in self.to_embed:
            _step.embed(embed_data)

        self.to_embed = []
        return _step

    def add_match(self, match):
        self.match_id += 1
        step = self.current_step
        step.location = str(match.location.filename) + ":" + str(match.location.line)

    def add_result(self, result):
        step = self.current_step
        step.add_result(result)

        if (
            self.is_last_step
            or result.status == Status.passed
            or result.status == Status.failed
            or result.status == Status.undefined
        ):
            self.status = result.status.name
            self.duration = self._scenario.duration

        # check if step execution finished
        # ebed to after_scenario_step if pseudo_steps enabled
        if self.is_last_step or result.status != Status.passed:
            self.steps_finished = True
            self.steps_finished_timestamp = time.time()

        return step

    def embed(self, embed_data):
        _step = self.current_step
        if _step is not None:
            _step.embed(embed_data)
        else:
            self.to_embed.append(embed_data)


class Step:
    def __init__(self, keyword, name, text, table, scenario):
        self.status = None
        self.duration = 0.0
        self.scenario = scenario
        self.keyword = keyword
        self.name = name
        self.text = text
        self.table = table
        self.location = ""
        self.location_link = None
        self.embeds = []

        self.commentary_override = False

    def add_result(self, result):
        self.status = result.status.name
        self.duration = result.duration

        # If the step has error message and step failed, set the error message.
        if result.error_message and result.status == Status.failed:
            self.error_message = result.error_message
            self.embed(
                Embed(
                    mime_type="text", data=self.error_message, caption="Error Message"
                )
            )

        # If the step is undefined use the behave function to provide information about it.
        if result.status == Status.undefined:
            undefined_step_message = (
                "\nYou can implement step definitions for undefined steps with "
            )
            undefined_step_message += "these snippets:\n\n"
            undefined_step_message += "\n".join(
                make_undefined_step_snippets(undefined_steps=[result])
            )

            self.error_message = undefined_step_message
            self.embed(
                Embed(
                    mime_type="text", data=self.error_message, caption="Error Message"
                )
            )

    def embed(self, embed_data):
        self.embeds.append(embed_data)

    def set_commentary(self, value=True):
        self.commentary_override = value


class Embed:
    def __init__(self, mime_type, data, caption=None, fail_only=False):
        self._mime_type = mime_type
        self._data = data
        self._caption = caption
        self._fail_only = fail_only

    def set_data(self, mime_type, data, caption=None):
        self._mime_type = mime_type
        self._data = data
        self._caption = caption

    def set_fail_only(self, fail_only):
        self._fail_only = fail_only


class Tag:
    def __init__(self, behave_tag, link=None):
        self.behave_tag = behave_tag
        self.link = link


# Heavily based on behave.formatter.json:JSONFormatter
# Since we need some form of structure from where we will pull all data upon close.
# Modifications based on our needs and experimentation.
class PrettyHTMLFormatter(Formatter):
    name = "html-pretty"
    description = "Pretty HTML formatter"
    title_string = "Test Suite Reporter"
    Embed = Embed
    pseudo_steps = False

    def __init__(self, stream, config):
        super(PrettyHTMLFormatter, self).__init__(stream, config)

        self.features = []

        self.high_contrast_button = False
        self.embed_number = 0
        self.table_number = 0

        self.suite_start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Some type of icon can be set.
        self.icon = None

        # This will return a stream given in behave call -o <file_name>.html.
        self.stream = self.open()

    def feature(self, feature):
        self.features.append(Feature(feature))

    @property
    def current_feature(self):
        if len(self.features) == 0:
            return None
        return self.features[-1]

    @property
    def current_scenario(self):
        if self.current_feature is None:
            return None
        if len(self.current_feature.scenarios) == 0:
            return None
        if self.scenario_finished:
            return None
        return self.current_feature.scenarios[-1]

    def before_scenario_finish(self, status):
        # Call this on Feature, as Scenario is not created yet.
        self.current_feature.before_scenario_finish(status)

    def after_scenario_finish(self, status):
        self.current_feature.after_scenario_finish(status)

    def scenario(self, scenario):
        self.scenario_finished = False
        self.current_feature.add_scenario(scenario, self.pseudo_steps)

    def step(self, step):
        self.current_scenario.add_step(step.keyword, step.name, step.text, step.table)

    def result(self, step):
        self.current_scenario.add_result(step)

    def match(self, match):
        # Executed before result.
        # Needed for knowing from where the code is coming from, instead of just location in the feature file.
        if match.location:
            self.current_scenario.add_match(match)

    def reset(self, reset):
        pass

    def uri(self, uri):
        pass

    def background(self, background):
        pass

    # Making bold text in between quotes.
    def make_bold_text(self, given_string):
        quote_count = given_string.count('"')

        # Save string to iterate over.
        the_rest = given_string
        for _ in range(int(quote_count / 2)):
            first_part, bold_text, the_rest = the_rest.split('"', 2)

            span(first_part)
            b(f'"{bold_text}"')

        span(the_rest)

    def embed(self, mime_type, data, caption=None, fail_only=False):
        embed_data = Embed(mime_type, data, caption, fail_only)
        # Find correct scenario.
        self.current_feature.embed(embed_data)
        return embed_data

    def set_title(self, title):
        self.title_string = title

    def set_icon(self, icon):
        self.icon = icon

    # Used to generate a steps.
    def generate_step(
        self,
        step_result,
        step_decorator,
        step_duration,
        step_link_label,
        step_link_location,
    ):

        with div(cls=f"step-capsule step-capsule-{step_result}"):

            with div(cls="step-status-decorator-duration-capsule"):
                with div(cls="step-status"):

                    # Behave defined status strings are "passed" "failed" "undefined" "skipped".
                    # Modify these values for high contrast usage.
                    high_contrast_status = {
                        "passed": "PASS",
                        "failed": "FAIL",
                        "undefined": "SKIP",
                        "skipped": "SKIP",
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

            # Make the link only when the link is provided
            if step_link_location:
                with div(cls="link"):
                    with a(href=step_link_location):
                        span(step_link_label)
            else:
                span(step_link_label)

    def generate_embed(self, embed_data):
        self.embed_number += 1

        caption = embed_data._caption
        mime_type = embed_data._mime_type
        data = embed_data._data

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

        # Check if the content of the data is a valid file - if so encode it to base64.
        if os.path.isfile(str(data)):
            data_base64 = base64.b64encode(open(data, "rb").read())
            data = data_base64.decode("utf-8").replace("\n", "")

        with div(cls="messages"):
            with div(cls="embed-capsule"):

                # Embed Caption.
                with div(cls="embed_button"):
                    with div(cls="link"):
                        # Label to be shown.
                        with a(
                            href="#/",
                            onclick=f"collapsible_toggle('embed_{self.embed_number}')",
                        ):
                            span(use_caption)

                # Actual Embed.
                if "video/webm" in mime_type:
                    with pre(cls="embed_content"):
                        with video(
                            id=f"embed_{self.embed_number}",
                            style="display: none",
                            width="1024",
                            controls="",
                        ):
                            source(
                                src=f"data:{mime_type};base64,{data}", type=mime_type
                            )

                if "image/png" in mime_type:
                    with pre(
                        cls="embed_content",
                        id=f"embed_{self.embed_number}",
                        style="display: none",
                    ):
                        img(src=f"data:{mime_type};base64,{data}")

                if "text" in mime_type:
                    with pre(
                        cls="embed_content",
                        id=f"embed_{self.embed_number}",
                        style="display: none",
                    ):
                        span(data)

                if "link" in mime_type:
                    with pre(
                        cls="embed_content",
                        id=f"embed_{self.embed_number}",
                        style="display: none",
                    ):
                        # FAF reports are coming in format set( [link, label], ... )
                        if type(data) is set:
                            for single_link in data:
                                with a(href=single_link[0]):
                                    span(single_link[1])
                        # If not 'set' lets assume the data is type list
                        else:
                            with a(href=data[0]):
                                span(data[1])

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

    def generate_text(self, given_text):
        with table():
            # Do not make the table header.
            with thead(onclick=f"collapsible_toggle('table_{self.table_number}')"):
                line = tr()
                line += th("Data")
            # Make the body.
            with tbody(id=f"table_{self.table_number}"):
                # Make rows.
                for row in given_text.split("\n"):
                    with tr() as line:
                        line += td(row)

        self.table_number += 1

    def generate_comment(self, commentary):
        # Generate commentary step.
        with div(cls=f"step-capsule step-capsule-commentary"):
            pre(f"{commentary}")

    def close(self):
        # Try block to be removed - debugging purposes only.
        try:
            # Generate everything.
            self.document = dominate.document(
                title=self.title_string, pretty_flags=True
            )

            # Iterate over the data and generate the page.
            with self.document.head:
                # Load and insert css theme.
                with open(
                    Path(__file__).parent / "theme.css", "r", encoding="utf-8"
                ) as _css_file:
                    css_theme = _css_file.read()
                with style(rel="stylesheet"):
                    raw(css_theme)

                # Load and insert javascript - important for embed toggles and high contrast switch.
                with open(
                    Path(__file__).parent / "script.js", "r", encoding="utf-8"
                ) as _script_file:
                    js_script = _script_file.read()
                with script(type="text/javascript"):
                    raw(js_script)

                ########## FEATURE FILE ITERATION ##########
                # Base structure for iterating over Features.
                for feature_id, feature in enumerate(self.features):
                    # Feature Panel
                    with div(cls="feature-panel"):
                        with div(cls="feature-icon-name-container"):
                            if self.icon:
                                with div(cls="feature-panel-icon"):
                                    img(src=self.icon)

                            # Generate content of the panel.
                            if not self.high_contrast_button:
                                # Making sure there is a functioning button.
                                with a(onclick=f"toggle_contrast('embed')", href="#"):
                                    # Creating the actual text content which is clickable.
                                    span(
                                        f"Feature: {feature.name} [High Contrast toggle]"
                                    )
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
                            with div(
                                cls=f"scenario-capsule scenario-capsule-{scenario.status}"
                            ):

                                for tag in scenario.tags:
                                    with div(cls="scenario-tags"):
                                        # Do not make links by default, this is handled on qecore side for links to bugzilla.
                                        # Tags come with structure [<tag>, None] or [<tag>, <bugzilla_link/git_link>]
                                        if tag.link is not None:
                                            with div(cls="link"):
                                                with a(href=tag.link):
                                                    span("@" + tag.behave_tag)
                                        else:
                                            span("@" + tag.behave_tag)

                                # Simple container for name + duration
                                with div(cls="scenario-info"):

                                    with div(cls="scenario-name"):
                                        span(f"Scenario: {scenario.name}")

                                    with div(cls="scenario-duration"):
                                        span(
                                            f"Scenario duration: {scenario.duration:.2f}s"
                                        )

                                ########## STEP ITERATION ##########
                                # Base structure for iterating over Steps in Scenarios.
                                steps = scenario.steps
                                if scenario.pseudo_steps:
                                    steps = (
                                        [scenario.pseudo_steps[0]]
                                        + steps
                                        + [scenario.pseudo_steps[1]]
                                    )
                                for step_id, step in enumerate(steps):
                                    # There was a request for a commentary step.
                                    # Such step would serve only as an information panel.
                                    if step.commentary_override:
                                        self.generate_comment(step.text)
                                    else:

                                        # Generate the step.
                                        step_result = (
                                            step.status if step.status else "skipped"
                                        )

                                        step_decorator = step.keyword + " " + step.name
                                        self.generate_step(
                                            step_result=step_result,
                                            step_decorator=step_decorator,
                                            step_duration=step.duration,
                                            step_link_label=step.location,
                                            step_link_location=step.location_link,
                                        )

                                        # Generate table for a step if present.
                                        if step.table is not None:
                                            self.generate_table(step.table)

                                        # Generate text field for a step if present.
                                        if step.text is not None:
                                            self.generate_text(step.text)

                                    # Generate all embeds that are in the data structure.
                                    # Add div for dashed-line last-child CSS selector.
                                    with div(cls="embeds"):
                                        for embed_data in step.embeds:
                                            if (
                                                embed_data._fail_only
                                                and scenario.status != "failed"
                                            ):
                                                continue
                                            self.generate_embed(embed_data=embed_data)

            # Write everything to the stream which should corelate to the -o <file> behave option.
            self.stream.write(self.document.render())

        except Exception:
            traceback.print_exc(file=sys.stdout)
