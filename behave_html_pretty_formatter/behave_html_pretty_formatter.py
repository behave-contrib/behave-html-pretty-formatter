"""
HTML Pretty formatter for behave
Inspired by https://github.com/Hargne/jest-html-reporter
"""

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
    """
    Simplified behave feature used by PrettyHTMLFormatter
    """

    def __init__(self, feature):
        self.name = feature.name
        self.description = feature.description
        self.location = feature.location
        self.status = Status.skipped.name
        self.icon = None
        self.high_contrast_button = False
        self.start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        self.scenarios = []
        self.to_embed = []
        self.scenario_finished = True
        self.scenario_begin_timestamp = time.time()
        self.before_scenario_duration = 0.0
        self.before_scenario_status = "skipped"

    def add_scenario(self, scenario, pseudo_steps=False):
        """
        Create new scenario in feature based on behave scenario object
        """
        self.scenario_finished = False
        _scenario = Scenario(scenario, self, pseudo_steps)
        for embed_data in self.to_embed:
            _scenario.embed(embed_data)
        self.to_embed = []
        # Stop embeding to before_scenario.
        _scenario.pseudo_step_id = 1

        if pseudo_steps:
            _step = _scenario.before_scenario_step
            _step.duration = self.before_scenario_duration
            _step.status = self.before_scenario_status

        self.scenarios.append(_scenario)
        return _scenario

    def embed(self, embed_data):
        """
        Embeds Data to current step in current scenario.
        """
        if not self.scenarios or self.scenario_finished:
            self.to_embed.append(embed_data)
        else:
            self.scenarios[-1].embed(embed_data)

    def before_scenario_finish(self, status):
        """
        Sets status and duration of before scenario pseudo step.
        """
        self.before_scenario_duration = time.time() - self.scenario_begin_timestamp
        self.before_scenario_status = status

    def after_scenario_finish(self, status):
        """
        Sets status and duration of after scenario presudo step.
        Should be called at the end of behave's `after_scenario()`,
        so that next embeds are correctly assigned to next scenario.
        """
        self.scenario_finished = True
        _scenario = self.scenarios[-1]
        _step = _scenario.after_scenario_step
        if _step is not None:
            if _scenario.steps_finished_timestamp:
                _step.duration = time.time() - _scenario.steps_finished_timestamp
            else:
                _step.duration = (
                    time.time()
                    - self.scenario_begin_timestamp
                    - self.before_scenario_duration
                )
            _step.status = status
            self.scenario_begin_timestamp = time.time()

    def generate_feature(self, formatter):
        """
        Converts this object to HTML.
        """
        # Feature Panel
        with div(cls="feature-panel"):
            with div(cls="feature-icon-name-container"):
                if self.icon:
                    with div(cls="feature-panel-icon"):
                        img(src=self.icon)

                # Generate content of the panel.
                if self.high_contrast_button:
                    # Making sure there is a functioning button.
                    with a(onclick="toggle_contrast('embed')", href="#"):
                        # Creating the actual text content which is clickable.
                        span(f"Feature: {self.name} [High Contrast toggle]")
                        # Set the flag to be sure there is not another one created.

                # On another feature do not generate the button.
                else:
                    span(f"Feature: {self.name}")

            # Suite started information.
            with div(cls="feature-timestamp"):
                span("Started: " + self.start_time)

        # Feature data container.
        with div(cls="feature-container"):

            for scenario in self.scenarios:
                scenario.generate_scenario(formatter)


class Scenario:
    """
    Simplified behaves's scenario.
    """

    def __init__(self, scenario, feature, pseudo_steps=False):
        self._scenario = scenario
        self.feature = feature
        self.name = scenario.name
        self.description = scenario.description
        self.pseudo_step_id = 0
        self.pseudo_steps = []
        if pseudo_steps:
            self.pseudo_steps = [
                Step(when, "scenario", None, None, self) for when in ("Before", "After")
            ]

        # We need another information about a tag, to recognize if it should act as a link or span.
        self.tags = [Tag(tag) for tag in scenario.effective_tags]

        self.location = scenario.location
        self.status = Status.skipped.name
        self.duration = 0.0
        self.match_id = -1
        self.steps_finished = False
        self.steps_finished_timestamp = None
        self.steps = []
        self.to_embed = []

        self.reported_error = None

        self.saved_matched_filename = None
        self.saved_matched_line = None
        # Process before_scenario errors.
        self.report_error(scenario)

    @property
    def before_scenario_step(self):
        """
        Access to before scenario pseudo step, if exists.
        """
        if self.pseudo_steps:
            return self.pseudo_steps[0]

        return None

    @property
    def after_scenario_step(self):
        """
        Access to before scenario pseudo step, if exists.
        """
        if self.pseudo_steps:
            return self.pseudo_steps[1]

        return None

    @property
    def current_step(self):
        """
        (Pseudo) Step currently being processed.
        Used mainly for correct embed tracking.
        """
        _step = None
        if self.match_id < 0:
            if self.pseudo_steps:
                _step = self.pseudo_steps[self.pseudo_step_id]
            elif self.steps:
                _step = self.steps[0]

        if self.steps_finished:
            _step = self.after_scenario_step

        if _step is None and self.steps:
            _step = self.steps[self.match_id]

        return _step

    @property
    def is_last_step(self):
        """
        Is last step processed?
        """
        return self.match_id + 1 >= len(self.steps)

    def add_step(self, keyword, name, step_text=None, step_table=None):
        """
        Add step. Called when new scenario is processed.
        """
        _step = Step(keyword, name, step_text, step_table, self)
        self.steps.append(_step)
        for embed_data in self.to_embed:
            _step.embed(embed_data)

        self.to_embed = []
        return _step

    def add_match(self, match):
        """
        Process information about step that will be executed next.
        """
        self.match_id += 1
        step = self.current_step
        step.location = str(match.location.filename) + ":" + str(match.location.line)

    def add_result(self, result):
        """
        Process information about executed step.
        """
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

    def report_error(self, behave_obj):
        """
        Embeds error message and traceback.
        """
        if not behave_obj.error_message:
            return
        if self.reported_error:
            if self.reported_error.data == behave_obj.error_message:
                return
            if self.reported_error.data in behave_obj.error_message:
                # Do not update traceback, as behave saves only first traceback.
                self.reported_error.data = behave_obj.error_message
                return
        self.reported_error = Embed("text", behave_obj.error_message, "Error Message")
        self.embed(self.reported_error)
        if "Traceback" not in behave_obj.error_message:
            self.embed(
                Embed(
                    "text",
                    traceback.format_exception(
                        type(behave_obj.exception),
                        behave_obj.exception,
                        behave_obj.exc_traceback,
                    ),
                    "Error Traceback",
                )
            )
        self.status = Status.failed.name

    def embed(self, embed_data):
        """
        Embed data to the this step.
        """
        _step = self.current_step
        if _step is not None:
            _step.embed(embed_data)
        else:
            self.to_embed.append(embed_data)

    def generate_scenario(self, formatter):
        """
        Converts scenario to HTML.
        """
        # Check for after_scenario errors.
        self.report_error(self._scenario)
        # Scenario container.
        with div(cls=f"scenario-capsule {self.status}"):

            for tag in self.tags:
                tag.generate_tag()

            # Simple container for name + duration
            with div(cls="scenario-info"):

                with div(cls="scenario-name"):
                    span(f"Scenario: {self.name}")

                with div(cls="scenario-duration"):
                    span(f"Scenario duration: {self.duration:.2f}s")

            steps = self.steps
            if self.pseudo_steps:
                steps = [self.pseudo_steps[0]] + steps + [self.pseudo_steps[1]]
            for step in steps:
                step.generate_step(formatter, self.status)


class Step:
    """
    Simplified behave step object.
    """

    def __init__(self, keyword, name, text, step_table, scenario):
        self.status = Status.skipped.name
        self.duration = 0.0
        self.scenario = scenario
        self.keyword = keyword
        self.name = name
        self.text = text
        self.table = step_table
        self.location = ""
        self.location_link = None
        self.embeds = []

        self.commentary_override = False

    def add_result(self, result):
        """
        Process result of the executed step.
        """
        self.status = result.status.name
        self.duration = result.duration

        # If the step has error message and step failed, set the error message.
        if result.error_message and result.status == Status.failed:
            self.scenario.report_error(result)

        # If the step is undefined use the behave function to provide information about it.
        if result.status == Status.undefined:
            undefined_step_message = (
                "\nYou can implement step definitions for undefined steps with "
            )
            undefined_step_message += "these snippets:\n\n"
            undefined_step_message += "\n".join(
                make_undefined_step_snippets(undefined_steps=[result])
            )

            self.embed(Embed("text", undefined_step_message, "Error Message"))

    def embed(self, embed_data):
        """
        Save new embed for this step.
        """
        self.embeds.append(embed_data)

    def set_commentary(self, value=True):
        """
        Turn this step into commentary step (or back to normal step).
        """
        self.commentary_override = value

    def generate_step(self, formatter, scenario_status):
        """
        Converts Step Object into HTML.
        """
        if self.commentary_override:
            with div(cls="step-capsule commentary"):
                pre(f"{self.text}")
        else:
            step_cls = f"step-capsule {self.status}"
            if self.keyword == "Before":
                step_cls = f"{step_cls} margin-bottom"
            if self.keyword == "After":
                step_cls = f"{step_cls} margin-top"
            with div(cls=step_cls):

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
                        span(high_contrast_status[self.status])

                    with div(cls="step-decorator"):
                        # Step decorator.
                        b(self.keyword)
                        formatter.make_bold_text(self.name)

                    with div(cls="step-duration"):
                        short_duration = f"{self.duration:.2f}s"
                        # Step duration.
                        span(f"({short_duration})")

                # Make the link only when the link is provided
                if self.location_link:
                    with div(cls="link"):
                        with a(href=self.location_link):
                            span(self.location)
                else:
                    span(self.location)
            # Still in non-commentary
            self.generate_text()
            self.generate_table()

        # Generate all embeds that are in the data structure.
        # Add div for dashed-line last-child CSS selector.
        with div(cls="embeds"):
            for embed_data in self.embeds:
                if embed_data.fail_only and scenario_status != "failed":
                    continue
                self.generate_embed(embed_data)

    def generate_embed(self, embed_data):
        """
        Converts embed data into HTML.

        This should not be part of Embed class, as Embed objects are
        returned to user for later modification of data, we want to
        prevent accidental call of this.
        """

        caption = embed_data.caption
        mime_type = embed_data.mime_type
        data = embed_data.data

        # If caption is user defined.
        if caption is not None:
            use_caption = caption
        # If caption is not defined try to use default one for specific mime type.
        elif mime_type in DEFAULT_CAPTION_FOR_MIME_TYPE:
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
                            onclick=f"collapsible_toggle('embed_{embed_data.uid}')",
                        ):
                            span(use_caption)

                # Actual Embed.
                if "video/webm" in mime_type:
                    with pre(cls="embed_content"):
                        with video(
                            id=f"embed_{embed_data.uid}",
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
                        id=f"embed_{embed_data.uid}",
                        style="display: none",
                    ):
                        img(src=f"data:{mime_type};base64,{data}")

                if "text" in mime_type:
                    with pre(
                        cls="embed_content",
                        id=f"embed_{embed_data.uid}",
                        style="display: none",
                    ):
                        span(data)

                if "link" in mime_type:
                    with pre(
                        cls="embed_content",
                        id=f"embed_{embed_data.uid}",
                        style="display: none",
                    ):
                        # FAF reports are coming in format set( [link, label], ... )
                        if isinstance(data, set):
                            for single_link in data:
                                with a(href=single_link[0]):
                                    span(single_link[1])
                        # If not 'set' lets assume the data is type list
                        else:
                            with a(href=data[0]):
                                span(data[1])

    def generate_table(self):
        """
        Converts step table into HTML.
        """
        if not self.table:
            return
        table_headings = self.table.headings
        table_rows = self.table.rows

        # Generate Table.
        with table():

            # Make a heading.
            with thead(
                onclick=f"collapsible_toggle('table_{PrettyHTMLFormatter.table_number}')"
            ):
                line = tr()
                for heading in table_headings:
                    line += th(heading)

            # Make the body.
            with tbody(id=f"table_{PrettyHTMLFormatter.table_number}"):
                for row in table_rows:
                    with tr() as line:
                        for cell in row:
                            line += td(cell)

        PrettyHTMLFormatter.table_number += 1

    def generate_text(self):
        """
        Converts step text into HTML.
        """
        if not self.text:
            return
        with table():
            # Do not make the table header.
            with thead(
                onclick=f"collapsible_toggle('table_{PrettyHTMLFormatter.table_number}')"
            ):
                line = tr()
                line += th("Text")
            # Make the body.
            with tbody(id=f"table_{PrettyHTMLFormatter.table_number}"):
                # Make rows.
                for row in self.text.split("\n"):
                    with tr() as line:
                        line += td(row)

        PrettyHTMLFormatter.table_number += 1


class Embed:
    """
    Encapsulates data to be embedded to the step.
    """

    count = 0

    def __init__(self, mime_type, data, caption=None, fail_only=False):
        self._id = Embed.count
        Embed.count += 1
        self._mime_type = mime_type
        self._data = data
        self._caption = caption
        self._fail_only = fail_only

    def set_data(self, mime_type, data, caption=None):
        """
        Set data, mime_type and caption.
        """
        self.mime_type = mime_type
        self.data = data
        self.caption = caption

    def set_fail_only(self, fail_only):
        """
        Set fail_only flag, whether embed should be done on pass or not.
        """
        self._fail_only = fail_only

    @property
    def mime_type(self):
        "Read-only mime_type access."
        return self._mime_type

    @property
    def data(self):
        "Read-only data access."
        return self._data

    @property
    def caption(self):
        "Read-only caption access."
        return self._caption

    @property
    def uid(self):
        """
        Read-only access for embed ID.
        """
        return self._id


class Tag:
    """
    Adds link to behave's tag
    """

    def __init__(self, behave_tag, link=None):
        self.behave_tag = behave_tag
        self._link = link

    def set_link(self, link):
        """
        Set link associated with tag.
        """

        assert isinstance(link, str), f"Link must be string, got {type(link)}"
        self._link = link

    def has_link(self):
        """
        Check if link is already set.
        """
        return self._link is not None

    def generate_tag(self):
        """
        Converts tag to HTML.
        """

        with div(cls="scenario-tags"):
            # Do not make links by default,
            # this is handled on qecore side for links to bugzilla.
            # Tags come with structure [<tag>, None] or [<tag>, <bugzilla_link/git_link>]
            if self._link is not None:
                with div(cls="link"):
                    with a(href=self._link):
                        span("@" + self.behave_tag)
            else:
                span("@" + self.behave_tag)


# Heavily based on behave.formatter.json:JSONFormatter
# Since we need some form of structure from where we will pull all data upon close.
# Modifications based on our needs and experimentation.
class PrettyHTMLFormatter(Formatter):
    """
    Behave Pretty HTML Formatter
    """

    name = "html-pretty"
    description = "Pretty HTML formatter"
    table_number = 0

    def __init__(self, stream, config):
        super(PrettyHTMLFormatter, self).__init__(stream, config)

        self.features = []

        self.high_contrast_button = False

        self.suite_start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Some type of icon can be set.
        self.icon = None

        # This will return a stream given in behave call -o <file_name>.html.
        self.stream = self.open()

        config_path = f"behave.formatter.{self.name}"

        self.pseudo_steps = self._str_to_bool(
            config.userdata.get(f"{config_path}.pseudo_steps", "false")
        )

        self.title_string = config.userdata.get(
            f"{config_path}.title_string", "Test Suite Reporter"
        )

        self.pretty_output = self._str_to_bool(
            config.userdata.get(f"{config_path}.pretty_output", "true")
        )

    def _str_to_bool(self, value):
        assert value.lower() in ["true", "false", "yes", "no", "0", "1"]
        return value.lower() in ["true", "yes", "1"]

    def feature(self, feature):
        self.features.append(Feature(feature))

    @property
    def current_feature(self):
        """
        Currently executed feature, if any.
        """
        if len(self.features) == 0:
            return None
        return self.features[-1]

    @property
    def current_scenario(self):
        """
        Currently executed scenario, if any.
        """
        _feature = self.current_feature
        if not _feature or not _feature.scenarios or _feature.scenario_finished:
            return None
        return _feature.scenarios[-1]

    def before_scenario_finish(self, status):
        """
        Sets status and duration of before scenario pseudo step.
        """
        # Call this on Feature, as Scenario is not created yet.
        self.current_feature.before_scenario_finish(status)

    def after_scenario_finish(self, status):
        """
        Sets status and duration of after scenario presudo step.
        Should be called at the end of behave's `after_scenario()`,
        so that next embeds are correctly assigned to next scenario.
        """
        # Call this on Feature, to be consistent with before_scenario_finish.
        self.current_feature.after_scenario_finish(status)

    def scenario(self, scenario):
        """
        Processes new scenario. It is added to the current feature.
        """
        self.current_feature.add_scenario(scenario, self.pseudo_steps)

    def step(self, step):
        """
        Register new step for current scenario.
        """
        self.current_scenario.add_step(step.keyword, step.name, step.text, step.table)

    def match(self, match):
        """
        Step is mathced and will be executed next.
        """
        # Executed before result.
        # Needed for knowing from where the code is coming from,
        # instead of just location in the feature file.
        if match.location:
            self.current_scenario.add_match(match)

    def result(self, step):
        """
        Step execution is finished.
        """
        self.current_scenario.add_result(step)

    def reset(self, reset):
        """
        Reset.
        """

    def uri(self, uri):
        """
        URI.
        """

    def background(self, background):
        """
        Background call. Not used by this formatter.
        """

    def make_bold_text(self, given_string):
        """
        Turn string into HTML tags, make bold tex in between quotes.
        """
        quote_count = given_string.count('"')

        # Save string to iterate over.
        the_rest = given_string
        for _ in range(int(quote_count / 2)):
            first_part, bold_text, the_rest = the_rest.split('"', 2)

            span(first_part)
            b(f'"{bold_text}"')

        span(the_rest)

    def embed(self, mime_type, data, caption=None, fail_only=False):
        """
        Prepares Embed data and append it to the currently executed (pseudo) step.
        returns: Embbed
        """

        embed_data = Embed(mime_type, data, caption, fail_only)
        # Find correct scenario.
        self.current_feature.embed(embed_data)
        return embed_data

    def set_title(self, title):
        """
        Title setter.
        """
        self.title_string = title

    def set_icon(self, icon):
        """
        Icon setter.
        """
        self.icon = icon

    def close(self):
        # Try block to be removed - debugging purposes only.
        try:
            # Generate everything.
            document = dominate.document(title=self.title_string)

            # Iterate over the data and generate the page.
            with document.head:
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

                if self.features:
                    feature = self.features[0]
                    feature.icon = self.icon
                    feature.high_contrast_button = True
                for feature in self.features:
                    feature.generate_feature(self)

            # Write everything to the stream which should corelate to the -o <file> behave option.
            self.stream.write(document.render(pretty=self.pretty_output))

        except Exception:
            traceback.print_exc(file=sys.stdout)
