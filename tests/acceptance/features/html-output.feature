Feature: Make behave generate Pretty HTML as output

  As a package maintainer
  I want to execute the Pretty HTML Formatter and verify its output
  So that I can ensure integration and basic functionality.

  Scenario: Run behave with Pretty HTML Formatter
    Given a file named "behave.ini" with:
      """
      [behave.formatters]
      html-pretty = behave_html_pretty_formatter:PrettyHTMLFormatter
      """
    When I run "behave --format html-pretty --dry-run"
    Then it should pass
    And the command output should contain:
      """
      <!DOCTYPE html>
      <html>
      """
    And the command output should contain:
      """
      <head>
      <title>Test Suite Reporter</title>
      """
    And the command output should contain:
      """
      <meta content="text/html;charset=utf-8" http-equiv="content-type">
      """
    And the command output should contain:
      """
      <style rel="stylesheet">
      """
    And the command output should contain:
      """
      <script type="text/javascript">
      """
    And the command output should contain:
      """
      </script>
      </head>
      <body onload="body_onload();">
      """
    And the command output should contain:
      """
      </body>
      </html>
      """
