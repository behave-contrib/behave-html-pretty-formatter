@dummy_feature
Feature: Dummy Feature


  @dummy_scenario_pass
  Scenario: Dummy Scenario Pass
    * Dummy pass


  @dummy_scenario_pass_pseudo_steps
  Scenario: Dummy Scenario Pass Pseudo Steps
    * Dummy pass


  @dummy_scenario_undefined
  Scenario: Dummy Scenario Undefined
    * Dummy undefined


  @dummy_scenario_skip
  Scenario: Dummy Scenario Skip
    * Dummy skip


  @dummy_scenario_commentary
  Scenario: Dummy Scenario Commentary
    * Dummy pass
    * Commentary
      """
      This field is generated from decorator 'Commentary'
      Where you insert text and override step to not print its decorator.
      The text will get printed and will be seen, as you can see.
      """
    * Dummy pass


  @dummy_scenario_table_and_text
  Scenario: Dummy Scenario Table and Text
    * Dummy pass
    * Table Example:
      | Field    | Data         |
      | Number   | dummy_data   |
      | Number_1 | dummy_data_1 |
      | Number_2 | dummy_data_2 |
      | Number_3 | dummy_data_3 |
      | Number_3 | dummy_data_4 |
    * Dummy pass
    * Text Example:
      """
      Hello World
      Hello World Again
      """
    * Dummy pass


  @dummy_scenario_fail
  Scenario: Dummy Scenario Fail
    * Dummy fail

