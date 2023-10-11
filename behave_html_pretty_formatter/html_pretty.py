"""
HTML Pretty formatter for behave
Inspired by https://github.com/Hargne/jest-html-reporter
"""

from __future__ import absolute_import

import atexit
import base64
import gzip
import time
import traceback
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import dominate
import markdown
from behave.formatter.base import Formatter
from behave.model_core import Status
from behave.runner_util import make_undefined_step_snippets
from dominate.tags import (
    a,
    b,
    div,
    i,
    img,
    meta,
    pre,
    script,
    source,
    span,
    style,
    table,
    tbody,
    td,
    th,
    thead,
    tr,
    video,
)
from dominate.util import raw

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

    def __init__(self, feature, feature_counter):
        self.name = feature.name
        self.description = "\n".join(feature.description)
        self.location = feature.location
        self.status = Status.skipped
        self.icon = None
        self.tags = feature.tags
        self.high_contrast_button = False
        self.start_time = datetime.now()
        self.finish_time = datetime.now()
        self.counter = feature_counter

        self.scenarios = []
        self._background = None
        self.to_embed = []
        self.scenario_finished = True
        self.scenario_begin_timestamp = time.time()
        self.before_scenario_duration = 0.0
        self.before_scenario_status = Status.skipped

    def add_background(self, background):
        """
        Save steps common for all scenarios in feature.
        """
        self._background = background

    @property
    def background_steps(self):
        """
        Return steps common for all scenarios in feature.
        """
        _steps = []
        if self._background:
            _steps = self._background.steps
        return _steps

    def add_scenario(self, scenario, scenario_counter, pseudo_steps=False):
        """
        Create new scenario in feature based on behave scenario object
        """
        self.scenario_finished = False
        _scenario = Scenario(scenario, self, scenario_counter, pseudo_steps)
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
        Embeds data to current step in current scenario.
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
        self.before_scenario_status = Status.from_name(status)

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
            _step.status = Status.from_name(status)
            self.scenario_begin_timestamp = time.time()

    def get_feature_stats(self):
        """
        Compute scenario stats if trere are multiple scenarios.
        """
        stats = OrderedDict()

        # Show Passed Failed always, skip and undefined only when present.
        stats["Passed"] = 0
        stats["Failed"] = 0

        for scenario in self.scenarios:
            status = scenario.status.name.capitalize()
            if status in stats:
                stats[status] += 1
            else:
                stats[status] = 1

        return stats

    def generate_feature(self, formatter):
        """
        Converts this object to HTML.
        """

        # Feature Title.
        with div(cls="feature-title flex-gap"):
            # Generate icon if present.
            if self.icon:
                with div(cls="feature-icon"):
                    img(src=self.icon)

            # Generate content of the feature title bar.
            span(f"Feature: {self.name}")

            # Adding start time based on Issue #45.
            start_time = self.start_time.strftime(formatter.date_format)
            span(f"Started: {start_time}", cls="feature-started")

            if self.high_contrast_button:
                # Making sure there is a functioning button.
                # Creating Dark Mode toggle which is clickable.
                span(
                    "Dark mode",
                    cls="button flex-left-space",
                    id="dark_mode_toggle",
                    onclick="toggle_dark_mode()",
                    data_value="auto",
                    data_next_value="dark",
                )

                # Creating High Contrast toggle which is clickable.
                span(
                    "High contrast toggle",
                    cls="button",
                    id="high_contrast",
                    onclick="toggle_hash('high_contrast')",
                )

                # Creating Summary which is clickable.
                span(
                    "Summary",
                    cls="button",
                    id="summary",
                    onclick="toggle_hash('summary')",
                )

        # Generate summary.
        summary_collapse = "collapse"
        if formatter.show_summary:
            summary_collapse = ""
        with div(
            cls=f"feature-summary-container flex-gap {summary_collapse}",
            id=f"f{self.counter}",
        ):
            # Generating feature commentary.
            flex_left_space = "flex-left-space" if self.description else ""

            # with div(cls=""):
            if self.description:
                pre(
                    self.description,
                    cls="feature-summary-commentary",
                )

            # Generating Summary results.
            with div(cls=f"feature-summary-stats {flex_left_space}"):
                stats = self.get_feature_stats()

                for stat, value in stats.items():
                    div(
                        f"{stat}: {value}",
                        cls=f"feature-summary-row {stat.lower()}",
                    )

            # Generating Started/Duration/Finished message.
            with div(cls="feature-summary-stats flex-left-space"):
                div(
                    f"Started: {self.start_time.strftime(formatter.date_format)}",
                    cls="feature-summary-row",
                )
                duration = (self.finish_time - self.start_time).total_seconds()
                div(f"Duration: {duration:.2f}", cls="feature-summary-row")
                div(
                    f"Finished: {self.finish_time.strftime(formatter.date_format)}",
                    cls="feature-summary-row",
                )

            # Generating clickable buttons for collapsing/expanding.
            with div(cls="feature-summary-stats"):
                span(
                    "Expand All",
                    cls="button display-block",
                    onclick="expander('expand_all', this)",
                )
                span(
                    "Collapse All",
                    cls="button display-block",
                    onclick="expander('collapse_all', this)",
                )
                span(
                    "Expand All Failed",
                    cls="button display-block",
                    onclick="expander('expand_all_failed', this)",
                )

            if formatter.additional_info:
                with div(cls="feature-additional-info-container", id="additional-info"):
                    # Generating Additional info results
                    with div(cls="feature-additional-info"):
                        for key, item in formatter.additional_info.items():
                            div(
                                f"{key}: {item}",
                                cls=f"feature-additional-info-row {key.lower()}",
                            )

        # Feature data container.
        with div(cls="feature-container", id=f"f{self.counter}"):
            for scenario in self.scenarios:
                scenario.generate_scenario(formatter)


class Scenario:
    """
    Simplified behaves's scenario.
    """

    def __init__(self, scenario, feature, scenario_counter, pseudo_steps=False):
        self._scenario = scenario
        self.feature = feature
        self.name = scenario.name
        self.description = scenario.description
        self.pseudo_step_id = 0
        self.pseudo_steps = []
        self.counter = scenario_counter
        if pseudo_steps:
            self.pseudo_steps = [
                Step(when, "scenario", None, None, self) for when in ("Before", "After")
            ]
            self.pseudo_steps[1].margin_top = True

        # We need another information about a tag, to recognize if it
        # should act as a link or span.
        self.tags = [Tag(tag) for tag in feature.tags + scenario.tags]

        self.location = scenario.location

        if self._scenario.status:
            self.status = self._scenario.status
        else:
            self.status = Status.skipped

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

        # Process steps.
        background_steps = feature.background_steps
        for step in background_steps:
            self.add_step(step.keyword, step.name, step.text, step.table)
        if background_steps and self.pseudo_steps:
            self.steps[0].margin_top = True
        first_step = True
        for step in scenario.steps:
            self.add_step(step.keyword, step.name, step.text, step.table)
            if first_step and (background_steps or pseudo_steps):
                self.steps[-1].margin_top = True
            first_step = False

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
            if self.match_id < len(self.steps):
                _step = self.steps[self.match_id]
            else:
                _step = self.steps[-1]

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

        # If step is "undefined", match() is not called by behave.
        if result.status == Status.undefined:
            self.match_id += 1

        step = self.current_step
        step.add_result(result)

        if (
            self.is_last_step
            or result.status == Status.passed
            or result.status == Status.failed
            or result.status == Status.skipped
            or result.status == Status.undefined
        ):
            self.status = result.status
            self.duration = self._scenario.duration

        # Check if step execution finished.
        # Embed to after_scenario_step if pseudo_steps enabled.
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
                self.reported_error.set_data(
                    "text",
                    behave_obj.error_message,
                    "Error Message",
                )
                return
        self.reported_error = Embed("text", behave_obj.error_message, "Error Message")
        self.embed(self.reported_error)
        if "Traceback" not in behave_obj.error_message:
            self.embed(
                Embed(
                    "text",
                    "".join(
                        traceback.format_exception(
                            type(behave_obj.exception),
                            behave_obj.exception,
                            behave_obj.exc_traceback,
                        ),
                    ),
                    "Error Traceback",
                ),
            )
        self.status = Status.failed

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
        common_cls = f"{self.status.name} {formatter.get_collapse_cls('scenario')}"
        with div(
            cls=f"scenario-header {common_cls}",
            id=f"f{self.feature.counter}-s{self.counter}-h",
        ):
            for tag in self.tags:
                tag.generate_tag()

            # Simple container for name + duration.
            with div(cls="scenario-info"):
                div(
                    f"Scenario: {self.name}",
                    cls="scenario-name",
                    id=f"f{self.feature.counter}-s{self.counter}",
                    onclick="expand_this_only(this)",
                )

                div(f"Scenario duration: {self.duration:.2f}s", cls="scenario-duration")

        with div(
            cls=f"scenario-capsule {common_cls}",
            id=f"f{self.feature.counter}-s{self.counter}-c",
        ):
            # add scenario description as "commentary":
            scenario_description = "\n".join(self._scenario.description)
            if scenario_description:
                pre(
                    f"{scenario_description}",
                    cls="step-capsule description no-margin-top",
                )

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
        self.status = Status.untested
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
        self.margin_top = False

    def add_result(self, result):
        """
        Process result of the executed step.
        """
        self.status = result.status
        self.duration = result.duration

        # If the step has error message and step failed, set the error message.
        if result.error_message and result.status == Status.failed:
            self.scenario.report_error(result)

        # If the step is undefined use the behave function to provide
        # information about it.
        if result.status == Status.undefined:
            undefined_step_message = (
                "\nYou can implement step definitions for undefined steps with "
            )
            undefined_step_message += "these snippets:\n\n"
            undefined_step_message += "\n".join(
                make_undefined_step_snippets(undefined_steps=[result]),
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
        if self.status is Status.untested:
            if not formatter.show_unexecuted_steps:
                return
            self.status = Status.skipped

        margin_top_cls = ""
        if self.margin_top:
            margin_top_cls = "margin-top"

        if self.commentary_override:
            pre(f"{self.text}", cls=f"step-capsule commentary {margin_top_cls}")

        else:
            with div(cls=f"step-capsule {self.status.name} {margin_top_cls}"):
                # Behave defined status strings are:
                # "passed" "failed" "undefined" "skipped".
                # Modify these values for high contrast usage.
                # Step status for high contrast - "PASS" "FAIL" "SKIP".
                high_contrast_status = {
                    "passed": "PASS",
                    "failed": "FAIL",
                    "undefined": "SKIP",
                    "skipped": "SKIP",
                    "untested": "SKIP",
                }

                div(high_contrast_status[self.status.name], cls="step-status")

                # Step decorator.
                with div(cls="step-decorator"):
                    b(i(self.keyword + " "))
                    formatter.make_bold_text(self.name)

                # Step duration.
                short_duration = f"{self.duration:.2f}s"
                div(f"({short_duration})", cls="step-duration")

                # Make the link only when the link is provided.
                if self.location_link:
                    a(self.location, cls="flex-left-space", href=self.location_link)
                else:
                    span(self.location, cls="flex-left-space")

            # Still in non-commentary.
            self.generate_text(formatter)
            self.generate_table(formatter)

        # Generate all embeds that are in the data structure.
        # Add div for dashed-line last-child CSS selector.
        with div(cls="embeds"):
            for embed_data in self.embeds:
                if embed_data.fail_only and scenario_status != Status.failed:
                    continue
                self.generate_embed(formatter, embed_data)

    def generate_download_button(self, embed_data, data, use_caption, filename):
        """
        Creates Download button in HTML.

        This should not be part of Embed class, as Embed objects are
        returned to user for later modification of data, we want to
        prevent accidental call of this.
        """

        def _create_download_button():
            _filename = filename if filename else use_caption
            args = f"'embed_{embed_data.uid}','{_filename}'"
            onclick = f"download_embed({args})"
            with div():
                span(
                    "Download",
                    cls="button margin-bottom",
                    onclick=onclick,
                )

        # Rule for embed_data.download_button as None - default value.
        if embed_data.download_button is None:
            # Do not create button if there is mime type text with less then 20 lines.
            min_lines_button = 20
            if "text" in embed_data.mime_type and data.count("\n") < min_lines_button:
                return

            # Do not create button if the mime type is link.
            if "link" in embed_data.mime_type:
                return

            # In all other cases the button is valid.
            _create_download_button()

        # Rule for embed_data.download_button as True.
        elif embed_data.download_button:
            # Create download for all cases.
            _create_download_button()

    def generate_embed_content(self, mime_type, data, compress):
        """
        Generate content of the embed based on the mime_type.

        :param mime_type: Mime type of the data to embed.
        :type mime_type: str

        :param data: Data to be embedded.
        :type data: Unspecified.

        :param compres: Whether to compress the text data
        :type data: Unspecified.
        """

        # Actual Embed.
        if "video/webm" in mime_type:
            with video(
                width="1024",
                controls="",
            ):
                source(src=f"data:{mime_type};base64,{data}", type=mime_type)

        if "image/png" in mime_type:
            img(src=f"data:{mime_type};base64,{data}")

        if "text" in mime_type:
            if "markdown" in mime_type:
                data = markdown.markdown(data)
            # javascript will decompress data and render them, if small enough
            if compress == "auto":
                compress = len(data) > 48 * 1024
            if compress or "html" in mime_type or "markdown" in mime_type:
                show = len(data) < 1024 * 1024
                data = data.encode("utf-8")
                if compress:
                    data = gzip.compress(data)
                data_base64 = base64.b64encode(data).decode("utf-8").replace("\n", "")
                span(
                    cls="to_render",
                    data=data_base64,
                    show=str(show).lower(),
                    compressed=str(compress).lower(),
                )
            else:
                span(data)

        if "link" in mime_type:
            # expected format: set( [link, label], ... )
            for single_link in data:
                with div():
                    a(single_link[1], href=single_link[0])

    def generate_embed(self, formatter, embed_data):
        """
        Converts embed data into HTML.

        This should not be part of Embed class, as Embed objects are
        returned to user for later modification of data, we want to
        prevent accidental call of this.
        """

        caption = embed_data.caption
        mime_type = embed_data.mime_type
        data = embed_data.data
        compress = embed_data.compress
        filename = embed_data.filename

        # If caption is user defined.
        if caption is not None:
            use_caption = caption
        # If caption is not defined try to use default one for specific mime type.
        elif mime_type in DEFAULT_CAPTION_FOR_MIME_TYPE:
            use_caption = DEFAULT_CAPTION_FOR_MIME_TYPE[mime_type]
        # No caption and no default caption for given mime type.
        else:
            use_caption = "unknown-mime-type"
            data = "data removed"

        file_path = None
        # Do not try to check filename for long data
        # Leads to OSError on some filesystems
        filename_len_limit = 256
        if len(data) < filename_len_limit:
            try:
                file_path = Path(str(data))
                if not file_path.is_file():
                    file_path = None
            except OSError:
                file_path = None

        if file_path:
            try:
                with file_path.open("rb") as _file:
                    data = _file.read()
                    if "text" not in mime_type:
                        data_base64 = base64.b64encode(data)
                        data = data_base64.decode("utf-8").replace("\n", "")
                    else:
                        data = data.decode("utf-8")
            except ValueError as error:
                data = f"data removed: ValueError: '{error}'"

        with div(cls="messages"), div(cls="embed-capsule"):
            # Embed Caption.
            div(
                use_caption,
                cls=f"embed_button {formatter.get_collapse_cls('embed')}",
                id=f"embed_button_{embed_data.uid}",
                onclick=f"toggle_hash('{embed_data.uid}')",
            )

            # Embed content.
            with pre(
                cls=f"embed_content {formatter.get_collapse_cls('embed')}",
                id=f"embed_{embed_data.uid}",
            ):
                self.generate_download_button(embed_data, data, use_caption, filename)
                self.generate_embed_content(mime_type, data, compress)

    def generate_table(self, formatter):
        """
        Converts step table into HTML.
        """
        if not self.table:
            return
        table_headings = self.table.headings
        table_rows = self.table.rows

        # Generate Table.
        with table(cls="table"):
            # Make a heading.
            with thead(
                onclick="toggle_hash(" f"'table_{PrettyHTMLFormatter.table_number}')",
            ):
                line = tr()
                for heading in table_headings:
                    line += th(heading)

            # Make the body.
            with tbody(
                id=f"table_{PrettyHTMLFormatter.table_number}",
                cls=formatter.get_collapse_cls("table"),
            ):
                for row in table_rows:
                    line = tr()
                    for cell in row:
                        line += td(cell)

        PrettyHTMLFormatter.table_number += 1

    def generate_text(self, formatter):
        """
        Converts step text into HTML.
        """
        if not self.text:
            return
        with table(cls="table"):
            if formatter.collapse_text:
                with thead(
                    onclick="toggle_hash("
                    f"'table_{PrettyHTMLFormatter.table_number}')",
                ):
                    line = tr()
                    line += th("Text")
            # Make the body.
            with tbody(
                id=f"table_{PrettyHTMLFormatter.table_number}",
                cls=formatter.get_collapse_cls("text"),
            ):
                # Make rows.
                for row in self.text.split("\n"):
                    line = tr()
                    line += td(row)

        PrettyHTMLFormatter.table_number += 1


class Embed:
    """
    Encapsulates data to be embedded to the step.
    """

    count = 0

    def __init__(
        self,
        mime_type,
        data,
        caption=None,
        fail_only=False,
        *,
        download_button=None,
        filename=None,
        compress="auto",
    ):
        # Generating unique ID.
        self.uid = str(uuid.uuid4())[:4]
        self.set_data(mime_type, data, caption)
        self._fail_only = fail_only
        self._compress = compress
        self._filename = filename
        self.download_button = download_button

    def set_data(self, mime_type, data, caption=None):
        """
        Set data, mime_type and caption.
        """
        self._mime_type = mime_type
        # Check that link is in format: set([link, label], ...)
        if mime_type == "link":
            new_data = []
            for single_link in data:
                link, label = single_link
                new_data.append([link, label])
            data = new_data
        self._data = data
        self._caption = caption

    def set_fail_only(self, fail_only):
        """
        Set fail_only flag, whether embed should be done on pass or not.
        """
        self._fail_only = fail_only

    def set_filename(self, filename):
        """
        Set filename to be forced when download button is clicked.
        """
        self._filename = filename

    def set_compress(self, compress):
        """
        Set compress flag, whether the text embed should be compressed or not.
        True: always compress
        'auto': compress if greater than 48kB
        False: never compress

        This is ignored for non-text files.
        """
        self._compress = compress

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
    def fail_only(self):
        "Read-only fail_only access."
        return self._fail_only

    @property
    def filename(self):
        "Read-only filename access."
        return self._filename

    @property
    def compress(self):
        "Read-only compress access."
        return self._compress


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
        if not isinstance(link, str):
            type_error = f"Link must be 'string', got type '{type(link)}'"
            raise TypeError(type_error)
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
            # Do not make links by default, this is handled on qecore
            # side for links to bugzilla. Tags come with structure
            # [<tag>, None] or [<tag>, <bugzilla_link/git_link>].
            if self.has_link():
                a("@" + self.behave_tag, href=self._link)
            else:
                span("@" + self.behave_tag)


# Based on behave.formatter.json:JSONFormatter
# Since we need some form of structure from where we will pull all data upon close.
# Modifications based on our needs and experimentation.
class PrettyHTMLFormatter(Formatter):
    """
    Behave Pretty HTML Formatter
    """

    name = "html-pretty"
    description = "Pretty HTML Formatter"
    table_number = 0

    feature_counter = 0
    scenario_counter = 0

    def __init__(self, stream, config):
        super().__init__(stream, config)

        self.features = []

        self.high_contrast_button = False

        self.suite_start_time = datetime.now()

        self._closed = False

        # Some type of icon can be set.
        self.icon = None

        # This will return a stream given in behave call -o <file_name>.html.
        self.stream = self.open()

        config_path = f"behave.formatter.{self.name}"
        additional_info_path = "behave.additional-info."
        additional_info_path = "behave.additional-info."

        self.pseudo_steps = self._str_to_bool(
            config.userdata.get(f"{config_path}.pseudo_steps", "false"),
        )

        self.title_string = config.userdata.get(
            f"{config_path}.title_string",
            "Test Suite Reporter",
        )

        self.pretty_output = self._str_to_bool(
            config.userdata.get(f"{config_path}.pretty_output", "true"),
        )

        self.date_format = config.userdata.get(
            f"{config_path}.date_format",
            "%d-%m-%Y %H:%M:%S",
        )

        self.show_summary = self._str_to_bool(
            config.userdata.get(f"{config_path}.show_summary", "false"),
        )

        self.collapse = [
            i.lower()
            for i in config.userdata.get(f"{config_path}.collapse", "auto").split(",")
        ]
        if "all" in self.collapse or "auto" in self.collapse or "none" in self.collapse:
            if len(self.collapse) != 1:
                msg = (
                    "Can not specify 'all', 'none' or 'auto' collapse at the same time."
                )
                raise RuntimeError(msg)

        self.collapse_scenario = "scenario" in self.collapse or "all" in self.collapse
        # collapse embeds by default
        self.collapse_embed = (
            "embed" in self.collapse
            or "all" in self.collapse
            or "auto" in self.collapse
        )
        self.collapse_table = "table" in self.collapse or "all" in self.collapse
        self.collapse_text = "text" in self.collapse or "all" in self.collapse

        self.show_unexecuted_steps = self._str_to_bool(
            config.userdata.get(f"{config_path}.show_unexecuted_steps", "true"),
        )

        self.additional_info = {}

        for key, item in config.userdata.items():
            if key.startswith(additional_info_path):
                short_key = key.replace(additional_info_path, "")
                self.additional_info[short_key] = item

        atexit.register(self._force_close)

    def get_collapse_cls(self, item_type):
        """
        Return collapse html class for given item type based on current config.

        :param item_type: type of collapsible item
        :type item_type: str
        :return: "collapse" or "" based on current config.
        :rtype: str
        """
        collapse = getattr(self, f"collapse_{item_type}", False)
        return "collapse" if collapse else ""

    def _str_to_bool(self, value):
        accepted_values = str(["true", "false", "yes", "no", "0", "1"])
        if value.lower() not in accepted_values:
            value_error = (
                f"Value '{value.lower()}' was not in correct format '{accepted_values}'"
            )
            raise ValueError(value_error)

        return value.lower() in ["true", "yes", "1"]

    def feature(self, feature):
        current_feature = self.current_feature
        if current_feature:
            current_feature.finish_time = datetime.now()
        self.feature_counter += 1
        self.scenario_counter = 0
        self.features.append(Feature(feature, self.feature_counter))

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
        self.scenario_counter += 1
        self.current_feature.add_scenario(
            scenario,
            self.scenario_counter,
            self.pseudo_steps,
        )

    def step(self, step):
        """
        Register new step for current scenario.
        """
        # Not used, parsed in scenario().
        # self.current_scenario.add_step(step.keyword, step.name, step.text, step.table)

    def match(self, match):
        """
        Step is matched and will be executed next.
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
        Background call.
        """
        feature = self.current_feature
        if feature:
            feature.add_background(background)

    def make_bold_text(self, given_string):
        """
        Turn string into HTML tags, make bold text in between quotes.
        """
        quote_count = given_string.count('"')

        # Save string to iterate over.
        the_rest = given_string
        for _ in range(int(quote_count / 2)):
            first_part, bold_text, the_rest = the_rest.split('"', 2)

            span(first_part)
            b(f'"{bold_text}"')

        span(the_rest)

    def embed(
        self,
        mime_type,
        data,
        caption=None,
        fail_only=False,
        *,
        download_button=None,
        filename=None,
        compress="auto",
    ):
        """
        Prepares Embed data and append it to the currently executed (pseudo) step.
        returns: Embed
        """
        embed_data = Embed(
            mime_type,
            data,
            caption,
            fail_only,
            download_button=download_button,
            filename=filename,
            compress=compress,
        )
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

    def _add_unexecuted_scenario(self):
        class DummyStep:  # pylint: disable=too-few-public-methods
            """
            Dummy step setting minimum attributes,
            so formatter would not crash.
            """

            keyword = "Before"
            name = "scenario"
            location = None
            duration = None
            error_message = None
            text = None
            table = None
            status = Status.failed

        class DummyScenario:  # pylint: disable=too-few-public-methods
            """
            Dummy scenario setting minimum attributes,
            so formatter would not crash.
            """

            name = "Unknown scenario"
            effective_tags = []
            description = ""
            location = None
            steps = [DummyStep]
            error_message = None
            status = Status.failed

        feature = self.current_feature
        background = feature._background  # pylint: disable=protected-access
        feature.add_background(None)
        pseudo_steps = self.pseudo_steps
        self.pseudo_steps = False
        self.before_scenario_finish(Status.failed.name)
        self.scenario(DummyScenario)
        feature.add_background(background)
        self.pseudo_steps = pseudo_steps

    def _force_close(self):
        """
        Called by `atexit`, set status of last step to failed and `close()`.
        """
        feature = self.current_feature
        scenario = self.current_scenario
        if not scenario and feature:
            # Create unexecuted scenario, if there are unprocessed embeds.
            if feature.to_embed:
                self._add_unexecuted_scenario()
        # refresh scenario
        scenario = self.current_scenario
        if scenario:
            scenario.status = Status.failed
            step = scenario.current_step
            step.status = Status.failed
        self.close()

    def close(self):
        """
        Generates the entire html page with dominate.
        """
        if self._closed:
            return
        self._closed = True
        # Set finish time of the last feature.
        current_feature = self.current_feature
        if current_feature:
            current_feature.finish_time = datetime.now()

        # Create dominate document.
        document = dominate.document(title=self.title_string)

        # Generate the head of the html page.
        with document.head:
            # Set content and http-equiv - taken from the base html formatter.
            meta(content="text/html;charset=utf-8", http_equiv="content-type")

            # Load and insert css theme.
            css_fname = "behave.css" if self.pretty_output else "behave.min.css"
            css_path = Path(__file__).parent / css_fname
            with css_path.open("r", encoding="utf-8") as _css_file:
                css_theme = _css_file.read()
            with style(rel="stylesheet"):
                raw(css_theme)

            # Load and insert javascript - important for embed toggles
            # and high contrast switch.
            js_fname = "behave.js" if self.pretty_output else "behave.min.js"
            js_path = Path(__file__).parent / js_fname
            with js_path.open("r", encoding="utf-8") as _script_file:
                js_script = _script_file.read()
            with script(type="text/javascript"):
                raw(js_script)

        # Iterate over the data and generate the page.
        with document.body as body:
            body.attributes["onload"] = "body_onload();"
            if self.features:
                feature = self.features[0]
                feature.icon = self.icon
                feature.high_contrast_button = True
            for feature in self.features:
                feature.generate_feature(self)

        # Write everything to the stream which corelates to the -o <file> behave option.
        self.stream.write(document.render(pretty=self.pretty_output))
