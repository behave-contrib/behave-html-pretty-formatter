# -*- coding: utf-8 -*-
"""
HTML formatter for behave.
Writes a single-page HTML file for test run with all features/scenarios.


IMPROVEMENTS:
  + Avoid to use lxml.etree, use xml.etree.ElementTree instead (bundled w/ Python)
  + Add pretty_print functionality to provide lxml goodie.
  + Stylesheet should be (easily) replacable
  + Simplify collapsable-section usage:
    => Only JavaScript-call: onclick = Collapsible_toggle('xxx')
    => Avoid code duplications, make HTML more readable
  + Expand All / Collapse All: Use <a> instead of <span> element
    => Make active logic (actions) more visible
  * Support external stylesheet ?!?
  * Introduce (Html)Page class to simplify extension and replacements
  * Separate business layer (HtmlFormatter) from technology layer (Page).
  * Correct Python2 constructs: map()/reduce()
  * end() or stream.close() handling is missing
  * steps: text, table parts are no so easily detectable
  * CSS: stylesheet should contain logical "style" classes.
    => AVOID using combination of style attributes where style is better.
  * Set custom title

TODO:
  * Embedding only works with one part ?!?
  * Even empty embed elements are contained ?!?
"""

import xml.etree.ElementTree as ET

from collections import Counter
from os.path import abspath
from pathlib import Path
from sys import version

from xml.dom import minidom
import re

import six

from behave.formatter.base import Formatter


def _valid_XML_char_ordinal(i):
    return (  # conditions ordered by presumed frequency
        0x20 <= i <= 0xD7FF
        or i in (0x9, 0xA, 0xD)
        or 0xE000 <= i <= 0xFFFD
        or 0x10000 <= i <= 0x10FFFF
    )


def ET_tostring(elem, pretty_print=False):
    """Render an HTML element(tree) and optionally pretty-print it."""

    text = ET.tostring(elem, "utf-8" if version < "3.0" else "unicode")
    if pretty_print:
        # -- RECIPE: For pretty-printing w/ xml.etree.ElementTree.
        # SEE: http://pymotw.com/2/xml/etree/ElementTree/create.html

        declaration_len = len(minidom.Document().toxml())
        reparsed = minidom.parseString(text)
        text = reparsed.toprettyxml(indent="  ")[declaration_len:]
        text_re = re.compile(r">\n\s+([^<>\s].*?)\n\s+</", re.DOTALL)
        text = text_re.sub(r">\g<1></", text)
    return text


class JavascriptLibrary:
    """
    Load minified javascript
    XXX
    """

    with open(Path(__file__).parent / "behave.min.js", encoding="utf-8") as js_file:
        collapsible = "\n" + js_file.read() + "\n"


class BasicTheme:
    """
    Load minified CSS
    XXX
    """

    with open(Path(__file__).parent / "behave.min.css", encoding="utf-8") as css_file:
        stylesheet_text = "\n" + css_file.read() + "\n"


class Page:
    """
    Provides a HTML page construct (as technological layer).
    XXX
    """

    theme = BasicTheme

    def __init__(self, title=None):
        pass


class HTMLFormatter(Formatter):
    """Provides a single-page HTML formatter
    that writes the result of a  test run.
    """

    name = "html"
    description = "Very basic HTML formatter"
    title = "Behave Test Report"

    def __init__(self, stream, config):
        super().__init__(stream, config)

        # -- XXX-JE-PREPARED-BUT-DISABLED:
        # XXX Seldom changed value.
        # XXX Should only be in configuration-file in own section
        #     "behave.formatter.html" ?!?
        # XXX Config support must be provided.
        # XXX REASON: Don't clutter behave config-space w/ formatter/plugin
        #     related config data.
        # self.css = self.default_css
        # if config.css is not None:
        #    self.css = config.css
        self.html = ET.Element("html")
        head = ET.SubElement(self.html, "head")
        ET.SubElement(head, "title").text = self.title
        ET.SubElement(
            head,
            "meta",
            {
                "content": "text/html;charset=utf-8",
                "http-equiv": "content-type",
            },
        )
        style = ET.SubElement(head, "style", type="text/css")
        style.append(ET.Comment(Page.theme.stylesheet_text))
        script = ET.SubElement(head, "script", type="text/javascript")
        script_text = ET.Comment(JavascriptLibrary.collapsible)
        script.append(script_text)

        self.stream = self.open()
        body = ET.SubElement(self.html, "body")
        self.suite = ET.SubElement(body, "div", {"class": "behave"})

        # Summary
        self.header = ET.SubElement(self.suite, "div", id="behave-header")
        label = ET.SubElement(self.header, "div", id="label")
        self.title_el = ET.SubElement(label, "h1")
        self.title_el.text = self.title

        summary = ET.SubElement(self.header, "div", id="summary")

        totals = ET.SubElement(summary, "p", id="totals")

        self.current_feature_totals = ET.SubElement(totals, "p", id="feature_totals")
        self.scenario_totals = ET.SubElement(totals, "p", id="scenario_totals")
        self.step_totals = ET.SubElement(totals, "p", id="step_totals")
        self.duration = ET.SubElement(summary, "p", id="duration")

        # -- PART: Expand/Collapse All
        expand_collapse = ET.SubElement(summary, "div", id="expand-collapse")
        expander = ET.SubElement(expand_collapse, "a", id="expander", href="#")
        expander.set("onclick", "Collapsible_expandAll('scenario_steps')")
        expander.text = "Expand All"
        cea_spacer = ET.SubElement(expand_collapse, "span")
        cea_spacer.text = " | "
        collapser = ET.SubElement(expand_collapse, "a", id="collapser", href="#")
        collapser.set("onclick", "Collapsible_collapseAll('scenario_steps')")
        collapser.text = "Collapse All"
        cea_spacer = ET.SubElement(expand_collapse, "span")
        cea_spacer.text = " | "
        expander = ET.SubElement(expand_collapse, "a", id="failed_expander", href="#")
        expander.set("onclick", "Collapsible_expandAllFailed()")
        expander.text = "Expand All Failed"

        self.embed_id = 0
        self.embed_in_this_step = None
        self.embed_data = None
        self.embed_mime_type = None
        self.last_scenario = None
        self.scenario_id = 0

    def feature(self, feature):
        if not hasattr(self, "all_features"):
            self.all_features = []
        self.all_features.append(feature)

        self.current_feature = ET.SubElement(self.suite, "div", {"class": "feature"})
        if feature.tags:
            tags_element = ET.SubElement(self.current_feature, "span", {"class": "tag"})
            tags_element.text = "@" + ", @".join(feature.tags)
        h2 = ET.SubElement(self.current_feature, "h2")
        feature_element = ET.SubElement(h2, "span", {"class": "val"})
        feature_element.text = f"{feature.keyword}: {feature.name}"
        if feature.description:
            description_element = ET.SubElement(
                self.current_feature, "pre", {"class": "message"}
            )
            description_element.text = "\n".join(feature.description)
        self.actual = {}
        self.actual["act_step_embed_span"] = ET.SubElement(self.current_feature, "span")

    def background(self, background):
        self.current_background = ET.SubElement(
            self.suite, "div", {"class": "background"}
        )

        h3 = ET.SubElement(self.current_background, "h3")
        ET.SubElement(
            h3, "span", {"class": "val"}
        ).text = f"{background.keyword}: {background.name}"

        self.steps = ET.SubElement(self.current_background, "ol")
        self.actual = {}
        self.actual["act_step_embed_span"] = ET.SubElement(
            self.current_background, "span"
        )

    def _check_last_scenario_status(self):
        if self.last_scenario is not None:
            if self.last_scenario.status == "failed":
                self.scenario_name.set("class", "failed")
                self.header.set("class", "failed")
                if self.last_scenario.error_message:
                    self.embedding(
                        "text/plain",
                        self.last_scenario.error_message,
                        "Scenario Error Message",
                    )

            if self.last_scenario.status == "undefined":
                self.scenario_name.set("class", "undefined")
                self.header.set("class", "undefined")

    def scenario(self, scenario):
        # check if self.last_scenario is failed
        self._check_last_scenario_status()

        if scenario.feature not in self.all_features:
            self.all_features.append(scenario.feature)
        self.scenario_el = ET.SubElement(self.suite, "div", {"class": "scenario"})

        scenario_file = ET.SubElement(
            self.scenario_el, "span", {"class": "scenario_file"}
        )
        scenario_file.text = f"{scenario.location.filename}:{scenario.location.line}"

        if scenario.tags:
            tags = ET.SubElement(self.scenario_el, "span", {"class": "tag"})
            tags.text = "@" + ", @".join(scenario.tags)

        self.scenario_name = ET.SubElement(self.scenario_el, "h3")
        span = ET.SubElement(self.scenario_name, "span", {"class": "val"})
        span.text = f"{scenario.keyword}: {scenario.name}"

        if scenario.description:
            description_element = ET.SubElement(
                self.scenario_el, "pre", {"class": "message"}
            )
            description_element.text = "\n".join(scenario.description)

        self.steps = ET.SubElement(
            self.scenario_el,
            "ol",
            {"class": "scenario_steps", "id": f"scenario_{self.scenario_id}"},
        )

        self.scenario_name.set(
            "onclick", f"Collapsible_toggle('scenario_{self.scenario_id}')"
        )
        self.scenario_id += 1

        self.last_scenario = scenario
        self.first_step = None
        self.current = None
        self.actual = {}
        self.actual["act_step_embed_span"] = ET.SubElement(self.scenario_el, "span")
        if scenario.error_message:
            self.embedding("text/plain", scenario.error_message, "Error Message")

    def scenario_outline(self, outline):
        """Scenario Outline formatter"""

        self.scenario(outline)
        self.scenario_el.set("class", "scenario outline")

    def step(self, step):

        cur = {}

        if self.first_step is None:
            self.first_step = cur
        else:
            self.current["next_step"] = cur

        cur["name"] = step.name
        cur["next_step"] = None
        cur["keyword"] = step.keyword

        self.current = cur

    def match(self, match):
        if self.actual is None or self.actual.get("next_step", None) is None:
            self.actual = self.first_step
        else:
            self.actual = self.actual["next_step"]

        step_el = ET.SubElement(self.steps, "li")
        step_name = ET.SubElement(step_el, "div", {"class": "step_name"})

        keyword = ET.SubElement(step_name, "span", {"class": "keyword"})
        keyword.text = self.actual["keyword"] + " "

        step_text = ET.SubElement(step_name, "span", {"class": "step val"})

        step_duration = ET.SubElement(step_name, "small", {"class": "step_duration"})

        step_file = ET.SubElement(step_el, "div", {"class": "step_file"})

        self.actual["act_step_embed_span"] = ET.SubElement(step_el, "span")
        self.actual["act_step_embed_span"].set("class", "embed")

        self.actual["step_el"] = step_el

        self.actual["step_duration_el"] = step_duration

        if match.arguments:
            text_start = 0
            for argument in match.arguments:
                step_part = ET.SubElement(step_text, "span")
                step_part.text = self.actual["name"][text_start : argument.start]
                ET.SubElement(step_text, "b").text = str(argument.value)
                text_start = argument.end
            step_part = ET.SubElement(step_text, "span")
            step_part.text = self.actual["name"][match.arguments[-1].end :]
        else:
            step_text.text = self.actual["name"]

        if match.location:
            if match.location.filename.startswith("../"):
                fname = abspath(match.location.filename)
            else:
                fname = match.location.filename
            location = f"{fname}:{match.location.line}"
        else:
            location = "<unknown>"
        ET.SubElement(step_file, "span").text = location

    def result(self, step):

        self.actual["step_el"].set("class", f"step {step.status.name}")

        self.actual["step_duration_el"].text = f"({step.duration:0.3f}s)"

        if step.text:
            message = ET.Element("div", {"class": "message"})
            self.actual["step_el"].insert(2, message)
            pre = ET.SubElement(message, "pre")
            pre.text = step.text

        if step.table:
            table = ET.Element("table")
            self.actual["step_el"].insert(2, table)
            tr = ET.SubElement(table, "tr")
            for heading in step.table.headings:
                ET.SubElement(tr, "th").text = heading

            for row in step.table.rows:
                tr = ET.SubElement(table, "tr")
                for cell in row.cells:
                    ET.SubElement(tr, "td").text = cell

        if step.error_message:
            self.embedding("text/plain", step.error_message, "Error Message")

        if step.status == "failed":
            self.scenario_name.set("class", "failed")
            self.header.set("class", "failed")

        if step.status == "undefined":
            self.scenario_name.set("class", "undefined")
            self.header.set("class", "undefined")

    def _doEmbed(self, span, mime_type, data, caption):
        self.embed_id += 1

        link = ET.SubElement(span, "a")
        link.set("onclick", f"Collapsible_toggle('embed_{self.embed_id}')")

        if "video/" in mime_type:
            if not caption:
                caption = "Video"
            link.text = six.u(caption)

            embed = ET.SubElement(
                span,
                "video",
                {
                    "id": f"embed_{self.embed_id}",
                    "style": "display: none",
                    "width": "1024",
                    "controls": "",
                },
            )
            embed.tail = "    "
            ET.SubElement(
                embed,
                "source",
                {"src": f"data:{mime_type};base64,{data}", "type": mime_type},
            )

        if "image/" in mime_type:
            if not caption:
                caption = "Screenshot"
            link.text = six.u(caption)

            embed = ET.SubElement(
                span,
                "img",
                {
                    "id": f"embed_{self.embed_id}",
                    "style": "display: none",
                    "src": f"data:{mime_type};base64,{data}",
                },
            )
            embed.tail = "    "

        if "text/" in mime_type:
            if not caption:
                caption = "Data"
            link.text = six.u(caption)

            cleaned_data = "".join(c for c in data if _valid_XML_char_ordinal(ord(c)))

            embed = ET.SubElement(
                span,
                "pre",
                {
                    "id": f"embed_{self.embed_id}",
                    "style": "display: none",
                },
            )
            embed.text = six.u(cleaned_data)
            embed.tail = "    "

        if mime_type == "link":
            if not caption:
                caption = "Link"
            link.text = six.u(caption)

            embed_div = ET.SubElement(
                span,
                "div",
                {
                    "id": f"embed_{self.embed_id}",
                    "style": "display: none",
                },
            )
            for single_link in data:
                ET.SubElement(embed_div, "br")
                embed_string = ET.SubElement(embed_div, "a")
                embed_string.set("href", single_link[0])
                embed_string.text = single_link[1]
            ET.SubElement(embed_div, "br")
            ET.SubElement(embed_div, "br")

    def embedding(self, mime_type, data, caption=None):
        """Append data to current step"""

        self._doEmbed(self.actual["act_step_embed_span"], mime_type, data, caption)

    def set_title(self, title, append=False, tag="span", **kwargs):
        """Set title of HTML file"""

        if not append:
            self.title_el.clear()
        ET.SubElement(self.title_el, tag, kwargs).text = title

    def close(self):
        if not hasattr(self, "all_features"):
            self.all_features = []
        self.duration.text = (
            f"Finished in {sum(x.duration for x in self.all_features):0.1f} seconds"
        )

        # check if self.last_scenario is failed
        self._check_last_scenario_status()

        # Filling in summary details
        result = []
        statuses = [x.status.name for x in self.all_features]
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append(f"{k}: {status_counter[k]}")
        self.current_feature_totals.text = "Features: " + ", ".join(result)

        result = []
        scenarios_list = [x.scenarios for x in self.all_features]
        scenarios = []
        if len(scenarios_list) > 0:
            scenarios = [x for subl in scenarios_list for x in subl]
        statuses = [x.status.name for x in scenarios]
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append(f"{k}: {status_counter[k]}")
        self.scenario_totals.text = "Scenarios: " + ", ".join(result)

        result = []
        step_list = [x.steps for x in scenarios]
        steps = []
        if step_list:
            steps = [x for subl in step_list for x in subl]
        statuses = [x.status.name for x in steps]
        status_counter = Counter(statuses)
        for k in status_counter:
            result.append(f"{k}: {status_counter[k]}")
        self.step_totals.text = "Steps: " + ", ".join(result)

        # Sending the report to stream
        if len(self.all_features) > 0:
            self.stream.write("<!DOCTYPE HTML>")
            self.stream.write(ET_tostring(self.html, pretty_print=False))
