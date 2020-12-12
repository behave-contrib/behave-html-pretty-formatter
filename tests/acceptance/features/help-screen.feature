Feature: Help screen

  As a tester
  I want to know whether the HTML formatter is configured
  So that I can verify I have integrated the formatter correctly.

  Scenario:
    Given a file named "behave.ini" with:
      """
      [behave.formatters]
      html = behave_html_formatter:HTMLFormatter
      """
    When I run "behave --format help"
    Then it should pass
    And the command output should contain:
      """
      Available formatters:
        html           Very basic HTML formatter
        json           JSON dump of test run
      """
