"""
Provides some command utility functions.
"""

import codecs

from hamcrest import assert_that, contains_string, equal_to, is_not
from hamcrest.core.helpers.hasmethod import hasmethod
from hamcrest.library.text.substringmatcher import SubstringMatcher

DEBUG = False


def template_substitute(text, **kwargs):
    """
    Replace placeholders in text by using the data mapping.
    Other placeholders that is not represented by data is left untouched.

    :param text:   Text to search and replace placeholders.
    :param data:   Data mapping/dict for placeholder key and values.
    :return: Potentially modified text with replaced placeholders.
    """
    for name, value in kwargs.items():
        placeholder_pattern = "{%s}" % name
        if placeholder_pattern in text:
            text = text.replace(placeholder_pattern, value)
    return text


def text_remove_empty_lines(text):
    """
    Whitespace normalization:

      - Strip empty lines
      - Strip trailing whitespace
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def text_normalize(text):
    """
    Whitespace normalization:

      - Strip empty lines
      - Strip leading whitespace  in a line
      - Strip trailing whitespace in a line
      - Normalize line endings
    """
    if isinstance(text, bytes):
        text = codecs.decode(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


class StringContainsMultipleTimes(SubstringMatcher):
    def __init__(self, substring, expected_count):
        super(StringContainsMultipleTimes, self).__init__(substring)
        self.expected_count = expected_count
        self.actual_count = 0

    def describe_to(self, description):
        description.append_text("a string ").append_text(
            self.relationship()
        ).append_text(" ").append_description_of(self.substring).append_text(
            " "
        ).append_description_of(
            self.expected_count
        ).append_text(
            " times instead of "
        ).append_description_of(
            self.actual_count
        )

    def _matches(self, item):
        if not hasmethod(item, "count"):
            return False
        self.actual_count = item.count(self.substring)
        return self.actual_count == self.expected_count

    def relationship(self):
        return "containing"


def contains_substring_multiple_times(substring, expected_count):
    return StringContainsMultipleTimes(substring, expected_count)


def assert_text_should_equal(actual_text, expected_text):
    assert_that(actual_text, equal_to(expected_text))


def assert_text_should_not_equal(actual_text, expected_text):
    assert_that(actual_text, is_not(equal_to(expected_text)))


def assert_text_should_contain_exactly(text, expected_part):
    assert_that(text, contains_string(expected_part))


def assert_text_should_not_contain_exactly(text, expected_part):
    assert_that(text, is_not(contains_string(expected_part)))


def assert_text_should_contain(text, expected_part):
    assert_that(text, contains_string(expected_part))


def assert_normtext_should_contain_multiple_times(text, expected_text, count):
    assert_that(text, contains_substring_multiple_times(expected_text, count))


def assert_text_should_not_contain(text, unexpected_part):
    assert_that(text, is_not(contains_string(unexpected_part)))


def assert_normtext_should_equal(actual_text, expected_text):
    expected_text2 = text_normalize(expected_text.strip())
    actual_text2 = text_normalize(actual_text.strip())
    assert_that(actual_text2, equal_to(expected_text2))


def assert_normtext_should_not_equal(actual_text, expected_text):
    expected_text2 = text_normalize(expected_text.strip())
    actual_text2 = text_normalize(actual_text.strip())
    assert_that(actual_text2, is_not(equal_to(expected_text2)))


def assert_normtext_should_contain(text, expected_part):
    expected_part2 = text_normalize(expected_part)
    actual_text = text_normalize(text.strip())
    if DEBUG:
        print("expected:\n{0}".format(expected_part2))
        print("actual:\n{0}".format(actual_text))
    assert_text_should_contain(actual_text, expected_part2)


def assert_normtext_should_not_contain(text, unexpected_part):
    unexpected_part2 = text_normalize(unexpected_part)
    actual_text = text_normalize(text.strip())
    if DEBUG:
        print("expected:\n{0}".format(unexpected_part2))
        print("actual:\n{0}".format(actual_text))
    assert_text_should_not_contain(actual_text, unexpected_part2)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
