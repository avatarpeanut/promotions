Feature: Promotions API
  As a store manager
  I need a RESTful catalogue service
  So that I can keep track of all my promotions

  Background:
    Given the following promotions
      | name         | promotion_type | discount_value | start_date | end_date   |
      | Summer Sale  | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
      | Black Friday | FIXED_AMOUNT   | 50.00          | 2026-11-27 | 2026-11-30 |

  # ---------------------------------------------------------------
  # Root / Service Discovery
  # ---------------------------------------------------------------

  Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Promotions Service" in the title
    And I should not see "404 Not Found"

  # ---------------------------------------------------------------
  # List Promotions
  # ---------------------------------------------------------------

  Scenario: List all promotions when none exist
    Given there are no promotions
    When I visit the "Home Page"
    And I press the "List" button
    Then I should see the message "No promotions found"
    And I should see 0 rows in the results table

  Scenario: List all promotions
    When I visit the "Home Page"
    And I press the "List" button
    Then I should see the message "Success"
    And I should see 2 rows in the results table
    And I should see "Summer Sale" in the results
    And I should see "Black Friday" in the results

  # ---------------------------------------------------------------
  # Query Promotions
  # ---------------------------------------------------------------

  Scenario: Query promotions by name
    Given the following promotions
      | name            | promotion_type | discount_value | start_date | end_date   |
      | Big Sale & More | BOGO           | 0.00           | 2026-07-01 | 2026-07-31 |
      | Black Friday    | FIXED_AMOUNT   | 50.00          | 2026-11-27 | 2026-11-30 |
    When I visit the "Home Page"
    And I set the "Name" to "Big Sale & More"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see 1 rows in the results table
    And I should see "Big Sale & More" in the results
    And I should not see "Black Friday" in the results

  Scenario: Query promotions by promotion type
    Given the following promotions
      | name         | promotion_type | discount_value | start_date | end_date   |
      | BOGO Special | BOGO           | 0.00           | 2026-07-01 | 2026-07-31 |
      | Summer Sale  | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I select "BOGO" in the "Type" dropdown
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see 1 rows in the results table
    And I should see "BOGO Special" in the results
    And I should not see "Summer Sale" in the results

  Scenario: Query promotions with no matching results
    When I visit the "Home Page"
    And I set the "Name" to "Missing Sale"
    And I press the "Search" button
    Then I should see the message "No promotions found"
    And I should see 0 rows in the results table

  # ---------------------------------------------------------------
  # Create Promotion
  # ---------------------------------------------------------------

  Scenario: Create a new promotion
    When I visit the "Home Page"
    And I set the "Name" to "July Sale"
    And I select "Percent Off" in the "Type" dropdown
    And I set the "Discount Value" to "10.00"
    And I set the "Start Date" to "2026-07-01"
    And I set the "End Date" to "2026-07-31"
    And I press the "Create" button
    Then I should see the message "Promotion has been Created!"
    When I copy the "Id" field
    And I press the "Clear" button
    Then the "Id" field should be empty
    And the "Name" field should be empty
    And I should see "Unknown" in the "Type" dropdown
    When I paste the "Id" field
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "July Sale" in the "Name" field
    And I should see "Percent Off" in the "Type" dropdown
    And I should see "10.00" in the "Discount Value" field
    And I should see "2026-07-01" in the "Start Date" field
    And I should see "2026-07-31" in the "End Date" field

  # ---------------------------------------------------------------
  # Read Promotion
  # ---------------------------------------------------------------

  Scenario: Read an existing promotion
    Given the following promotions
      | name        | promotion_type | discount_value | start_date | end_date   |
      | Summer Sale | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Retrieve" button
    Then I should see "Summer Sale" in the "Name" field
    And I should see "Percent Off" in the "Type" dropdown
    And I should see the message "Success"

  Scenario: Read a promotion that does not exist
    When I visit the "Home Page"
    And I set the "Id" to "0"
    And I press the "Retrieve" button
    Then I should see the message "Not Found"

  # ---------------------------------------------------------------
  # Update Promotion
  # ---------------------------------------------------------------

  Scenario: Update an existing promotion
    Given the following promotions
      | name        | promotion_type | discount_value | start_date | end_date   |
      | Summer Sale | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Retrieve" button
    And I set the "Name" to "Summer Sale Extended"
    And I set the "Discount Value" to "25.00"
    And I press the "Update" button
    Then I should see the message "Success"
    When I press the "Clear" button
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Retrieve" button
    Then I should see "Summer Sale Extended" in the "Name" field
    And I should see "25.00" in the "Discount Value" field

  Scenario: Update a promotion that does not exist
    When I visit the "Home Page"
    And I set the "Id" to "0"
    And I set the "Name" to "Ghost Promo"
    And I press the "Update" button
    Then I should see the message "Not Found"

  # ---------------------------------------------------------------
  # Delete Promotion
  # ---------------------------------------------------------------

  Scenario: Delete a promotion by searching by name
    Given the following promotions
      | name           | promotion_type | discount_value | start_date | end_date   |
      | Expired Coupon | PERCENT_OFF    | 10.00          | 2026-01-01 | 2026-01-31 |
    When I visit the "Home Page"
    And I set the "Name" to "Expired Coupon"
    And I press the "Search" button
    Then I should see "Expired Coupon" in the results
    When I set the "Promotion ID" to the last created promotion ID
    And I press the "Delete" button
    Then I should see the message "Promotion has been Deleted!"
    When I press the "Clear" button
    And I press the "List" button
    Then I should not see "Expired Coupon" in the results

  Scenario: Delete a promotion by ID then confirm it is gone
    Given the following promotions
      | name           | promotion_type | discount_value | start_date | end_date   |
      | Expired Coupon | PERCENT_OFF    | 10.00          | 2026-01-01 | 2026-01-31 |
    When I visit the "Home Page"
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Delete" button
    Then I should see the message "Promotion has been Deleted!"
    When I press the "Clear" button
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Retrieve" button
    Then I should see the message "Not Found"

  # ---------------------------------------------------------------
  # Deactivate Promotion
  # ---------------------------------------------------------------

  Scenario: Deactivate a promotion by searching by name
    Given the following promotions
      | name        | promotion_type | discount_value | start_date | end_date   |
      | Summer Sale | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I set the "Name" to "Summer Sale"
    And I press the "Search" button
    Then I should see "Summer Sale" in the results
    When I set the "Promotion ID" to the last created promotion ID
    And I press the "Deactivate" button
    Then I should see the message "Success"
    And I should see "false" in the results

  Scenario: Deactivate a promotion by retrieving by ID
    Given the following promotions
      | name        | promotion_type | discount_value | start_date | end_date   |
      | Summer Sale | PERCENT_OFF    | 20.00          | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I set the "Promotion ID" to the last created promotion ID
    And I press the "Retrieve" button
    Then I should see the message "Success"
    When I press the "Deactivate" button
    Then I should see the message "Success"
    When I press the "Retrieve" button
    Then I should see "false" in the results
