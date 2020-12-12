"""
Steps for behave tests
"""
from behave import given, when, then


@given(u'a file named "{filename}" with')
def step_file(context, filename):
    pass


@when(u'I run "{shellcommand}"')
def step_execute(context, shellcommand):
    pass


@then(u"it should pass")
def step_success(context):
    pass


@then(u"the command output should contain")
def step_result(context):
    pass
