Feature: Make behave generate HTML as output

  As a package maintainer
  I want to execute the HTML formatter and verify its output
  So that I can ensure integration and basic functionality.

  Scenario: Run behave with HTML formatter
    Given a file named "behave.ini" with:
      """
      [behave.formatters]
      html = behave_html_formatter:HTMLFormatter
      """
    When I run "behave --format html --dry-run"
    Then it should pass
    And the command output should contain:
      """
      <!DOCTYPE HTML><html>
      """
    And the command output should contain:
      """
      <head><title>Behave Test Report</title>
      """
    And the command output should contain:
      """
      <meta content="text/html;charset=utf-8" http-equiv="content-type" />
      """
    And the command output should contain:
      """
      <style type="text/css">
      """
    And the command output should contain:
      """
      </style><script type="text/javascript">
      """
    And the command output should contain:
      """
      </script></head><body>
      """
    And the command output should contain:
      """
      <h1>Behave Test Report</h1>
      """
    And the command output should contain:
      """
      </body></html>
      """
