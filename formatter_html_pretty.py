# Inspired by https://github.com/Hargne/jest-html-reporter

from __future__ import absolute_import
import sys
import traceback
from curses import raw
from posixpath import abspath
from datetime import datetime

import dominate
from dominate.tags import *
from dominate.util import raw

from behave.formatter.base import Formatter
from behave.model_core import Status
from behave.runner_util import make_undefined_step_snippets


PASS = "PASS"
FAIL = "FAIL"
UNDEFINED = "UNDEFINED"
SKIP_NOT_STARTED = "SKIP-NOT-STARTED"

DEFAULT_CAPTION_FOR_MIME_TYPE = {
    "video/webm": "Video",
    "image/png": "Screenshot",
    "text": "Data",
    "link": "Link",
}


# Heavily based on behave.formatter.json:JSONFormatter
# Since we need some form of structure from where we will pull all data upon close.
# Modifications based on our needs and experimentation.
class PrettyHTMLFormatter(Formatter):
    name = "html-pretty"
    description = "Pretty HTML formatter"

    def __init__(self, stream, config):
        super(PrettyHTMLFormatter, self).__init__(stream, config)

        self.feature_count = 0
        self.current_feature = None
        self.current_feature_id = self.feature_count
        self.current_feature_data = None

        self.scenario_count = 0
        self.current_scenario = None
        self.current_scenario_id = 0
        self.current_scenario_data = None

        self.step_count = 0
        self.current_step = None
        self.current_step_id = 0
        self.current_step_data = None

        self.step_result_count = 0

        self.data_structure = {}

        self.high_contrast_button = False
        self.embed_number = 0

        self.suite_start_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # Theory of what this will do:
        # This will return a stream given in behave call -o report.html.
        self.stream = self.open()


    def reset_scenario(self):
        self.current_scenario = None
        self.current_scenario_id = 0
        self.current_scenario_data = None

        self.step_count = 0
        self.current_step = None
        self.current_step_id = 0
        self.current_step_data = None

        self.step_result_count = 0


    def feature(self, feature):
        print("DEBUG, executing feature")
        self.current_feature = feature
        self.current_feature_id = self.feature_count
        self.current_feature_data = {
            "keyword": feature.keyword,
            "name": feature.name,
            "description": feature.description,
            "tags": feature.name,
            "location": feature.location, # TODO format
            "status": None,
            "scenarios": {},
        }

        self.data_structure[self.current_feature_id] = self.current_feature_data
        self.feature_count += 1


    def scenario(self, scenario):
        print("DEBUG, executing scenario")
        self.reset_scenario()

        self.current_scenario = scenario
        self.current_scenario_id = self.scenario_count

        scenario_to_add = {
            "keyword": scenario.keyword,
            "name": scenario.name,
            "description": scenario.description,
            "tags": scenario.tags,
            "location": scenario.location, # TODO format
            "steps": {},
            "status": None,
            "duration": 0.0
        }


        current_feature = self.data_structure[self.current_feature_id]["scenarios"]
        current_feature[self.current_scenario_id] = scenario_to_add
        self.scenario_count += 1


    def step(self, step):
        print("DEBUG, executing step")
        self.current_step = step
        self.current_step_id = self.step_count

        new_step_add = {
            "keyword": step.keyword,
            "step_type": step.step_type,
            "name": step.name,
            "location": f"{abspath(step.location.filename)}:{step.location.line}",
            "embed": {},
        }

        if step.table:
            data = {
                "headings": step.table.headings,
                "rows": [list(row) for row in step.table.rows]
            }
            new_step_add["table"] = data

        scenarios = self.data_structure[self.current_feature_id]["scenarios"]
        steps = scenarios[self.current_scenario_id]["steps"]
        steps[self.current_step_id] = new_step_add
        self.step_count += 1


    def result(self, step):
        print("DEBUG, executing result")
        # Try block to be removed - debugging purposes only.
        try:
            # Update the step based on its result.
            scenarios = self.data_structure[self.current_feature_id]["scenarios"]
            steps = scenarios[self.current_scenario_id]["steps"]
            steps[self.step_result_count]["result"] = {
                "status": step.status.name,
                "duration": step.duration,
            }

            # If the step has error message and step failed, set the error message to the data structure.
            if step.error_message and step.status == Status.failed:
                error_message = step.error_message
                result = steps[self.step_result_count]["result"]
                result["error_message"] = error_message

            # If the step is undefined use the behave function to provide information and save it to data structure.
            if step.status == Status.undefined:
                undefined_step_message = u"\nYou can implement step definitions for undefined steps with "
                undefined_step_message += u"these snippets:\n\n"
                undefined_step_message += u"\n".join(make_undefined_step_snippets(undefined_steps=[step]))

                error_message = undefined_step_message
                result = steps[self.step_result_count]["result"]
                result["error_message"] = error_message

            # If the last step was set.
            # If the step status is passed, failed or undefined.
            # Set the Scenario status as Step Status.
            scenario = self.data_structure[self.current_feature_id]["scenarios"][self.current_scenario_id]
            if self.step_result_count == self.step_count or\
                step.status == Status.passed or\
                step.status == Status.failed or\
                step.status == Status.undefined:
                scenario["status"] = step.status.name
                scenario["duration"] = self.current_scenario.duration

            # If the step has result and error message is in result, make sure to embed the error message.
            if "result" in steps[self.step_result_count] and\
                "error_message" in steps[self.step_result_count]["result"]:
                self.embedding(mime_type="text",
                               data=steps[self.step_result_count]["result"]["error_message"],
                               caption="Error Message")

            # If the step status is failed, undefined or skipped do not increase the counter.
            if not (step.status == Status.failed or\
                step.status == Status.skipped or\
                step.status == Status.undefined):
                self.step_result_count += 1

        except Exception:
            traceback.print_exc(file=sys.stdout)


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
        with div(cls="step-info"):
            with div(cls=f"step-capsule step-capsule-{step_result.lower()}"):

                with div(cls="step-status-decorator-duration"):
                    with div(cls="step-status"):
                        # Step status for high contrast.
                        span("SKIP" if step_result in (UNDEFINED, SKIP_NOT_STARTED) else step_result)

                    with div(cls="step-decorator"):
                        # Step decorator.
                        self.make_bold_text(step_decorator)

                    with div(cls="step-duration"):
                        short_duration = "{:.2f}s".format(step_duration)
                        # Step duration
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

        # Serves for css embed purpose for te dotted line after the last embed.
        last_embed = f"-last" if last else ""

        with div(cls=f"messages-{scenario_result}{last_embed}"):
            with div(cls="embed-info"):

                # Embed Caption.
                with div(cls="embed"):
                    with div(cls="link"):
                        # Label to be shown.
                        with a(onclick=f"collapsible_toggle('embed_{self.embed_number}')"):
                            span(use_caption)

                # Actual Embed.
                if "video/webm" in mime_type:
                    with pre(cls="message-content"):
                        with video(id=f"embed_{self.embed_number}", style="display: none", width="1024", controls=""):
                            source(src=f"data:{mime_type};base64,{data}    ", type=mime_type)

                if "image/png" in mime_type:
                    with pre(cls="message-content", id=f"embed_{self.embed_number}", style="display: none"):
                        img(src=f"data:{mime_type};base64,{data}    ")

                if "text" in mime_type:
                    with pre(cls="message-content", id=f"embed_{self.embed_number}", style="display: none"):
                        span(data)

                if "link" in mime_type:
                    with pre(cls="message-content", id=f"embed_{self.embed_number}", style="display: none"):
                        with a(href="http://google.com"):
                            span(data)


    def embedding(self, mime_type, data, caption=None, fail_only=False):
        # Find correct scenario.
        scenario = self.data_structure[self.current_feature_id]["scenarios"]

        # Find correct step to embed data to.
        if self.step_result_count in scenario[self.current_scenario_id]["steps"]:
            step = scenario[self.current_scenario_id]["steps"][self.step_result_count]
        else:
            step = scenario[self.current_scenario_id]["steps"][self.step_result_count - 1]

        # Actual embed structure.
        step_embed = step["embed"]

        # Enter the data.
        step_embed[self.embed_number] = {}
        step_embed[self.embed_number]["mime_type"] = mime_type
        step_embed[self.embed_number]["data"] = data
        step_embed[self.embed_number]["caption"] = caption
        step_embed[self.embed_number]["last"] = True

        # Since current step is alway 'last' set the previous 'last' to False.
        if (self.embed_number - 1) in step_embed:
            step_embed[self.embed_number - 1]["last"] = False

        # The current embed number is used, bump the counter.
        self.embed_number += 1


    def generate_table(self, given_table):
        table_headings = given_table["headings"]
        table_rows = given_table["rows"]

        # Generate Table.
        with table():

            # Make a heading.
            with thead():
                line = tr()
                for heading in table_headings:
                    line += th(heading)

            # Make the body.
            with tbody():
                for row in table_rows:
                    with tr() as line:
                        for cell in row:
                            line += td(cell)


    def close(self):
        # Try block to be removed - debugging purposes only.
        try:
            # Generate everything.
            self.document = dominate.document(title="Test Suite Reporter", pretty_flags=False)

            # Iterate over the data and generate the page.
            with self.document.head:
                # Load and insert css theme.
                with open("/usr/local/lib/python3.9/site-packages/formatter_html_pretty/improved.css", "r") as _css_file:
                    css_theme = _css_file.read()
                with style(rel="stylesheet"):
                    raw(css_theme)

                # Load and insert javascript - important for embed toggles and high contrast switch.
                with open("/usr/local/lib/python3.9/site-packages/formatter_html_pretty/script.js", "r") as _script_file:
                    js_script = _script_file.read()
                with script(type="text/javascript"):
                    raw(js_script)


                ########## FEATURE FILE ITERATION ##########
                # Base structure for iterating over Features.
                for feature_id, feature_data in self.data_structure.items():
                    # Feature Panel
                    with div(cls="suite-info"):
                        with div(cls="suite-path"):

                            feature_name = feature_data["name"]

                            # Generate first button.
                            if not self.high_contrast_button:
                                with a(onclick=f"toggle_contrast('embed')"):
                                    span(f"Feature: {feature_name} [click for High Contrast]")
                                    self.high_contrast_button = True

                            # On another feature do not generate.
                            else:
                                span(f"Feature: {feature_name}")

                        # Suite started information.
                        with div(cls="timestamp"):
                            span("Started: " + self.suite_start_time)

                    # Feature data container.
                    with div(cls="feature-container"):
                        with div(cls="suite-tests"):

                            ########## SCENARIOS ITERATION ##########
                            # Base structure for iterating over Scenarios in Features.
                            for scenario_id, scenario_data in feature_data["scenarios"].items():
                                # Scenario container.
                                print(scenario_data["status"])
                                scenario_status = scenario_data["status"] # passed/failed/undefined/skipped

                                with div(cls=f"scenario-capsule scenario-capsule-{scenario_status}"):

                                    for tag in scenario_data["tags"]:
                                        with div(cls="test-tags"):
                                            with div(cls="link"):
                                                # TODO LINK
                                                with a(href="http://google.com"):
                                                    span("@"+tag)

                                    scenario_name = scenario_data["name"]
                                    scenario_duration = "{:.2f}s".format(scenario_data["duration"])

                                    with div(cls="test-info"):
                                        with div(cls="test-suitename"):
                                            span(f"Scenario: {scenario_name}")

                                        with div(cls="test-duration"):
                                            span(f"Scenario duration: {scenario_duration}")

                                    ########## STEP ITERATION ##########
                                    # Base structure for iterating over Steps in Scenarios.
                                    for step_id, step in scenario_data["steps"].items():

                                        # The step has some result saved.
                                        if "result" in step:
                                            step_result = step["result"]["status"]
                                            step_decorator = step["keyword"] + " " + step["name"]
                                            step_duration = step["result"]["duration"]
                                            step_link = step["location"]
                                        # The step has no result therefore it was not executed and was skipped.
                                        else:
                                            step_result = "skipped"
                                            step_decorator = step["keyword"] + " " + step["name"]
                                            step_duration = float(0)
                                            step_link = step["location"]

                                        # Define result based on data, we have values for these because of high contrast.
                                        # There should be a more elegant solution to this, this works for now.
                                        if step_result == "passed":
                                            result_to_pass = PASS
                                        elif step_result == "failed":
                                            result_to_pass = FAIL
                                        elif step_result == "undefined":
                                            result_to_pass = UNDEFINED
                                        elif step_result == "skipped":
                                            result_to_pass = SKIP_NOT_STARTED
                                        else:
                                            result_to_pass = None

                                        # Generate the step.
                                        self.generate_step(
                                            step_result=result_to_pass,
                                            step_decorator=step_decorator,
                                            step_duration=step_duration,
                                            step_link_label=step_link,
                                            step_link_location="http://google.com" # TODO dynamic
                                        )

                                        # Generate table for a step if present.
                                        if "table" in step:
                                            self.generate_table(step["table"])

                                        # Generate all embeds that are in the data structure.
                                        for embed_id, embed_data in step["embed"].items():
                                            if "embed" in step and step["embed"] != {}:
                                                self.data_embeding_function(
                                                    mime_type=embed_data["mime_type"],
                                                    data=embed_data["data"],
                                                    caption=embed_data["caption"],
                                                    last=embed_data["last"],
                                                    scenario_result=step_result
                                                )

            # Write everything to the stream which should corelate to the -o <file> behave option.
            self.stream.write(self.document.render())

        except Exception:
            traceback.print_exc(file=sys.stdout)
