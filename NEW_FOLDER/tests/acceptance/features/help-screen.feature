Feature: List HTML formatter among the available formatters

  As a tester
  I want to know whether the HTML formatter is configured
  So that I can verify I have integrated it correctly.

  Scenario: List available formatters
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
