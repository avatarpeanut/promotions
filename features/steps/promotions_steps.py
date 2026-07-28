"""
Step definitions for Promotions API BDD tests
"""

import requests
from compare3 import expect
from behave import given
from service.common import status  # HTTP Status Codes
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

WAIT_TIMEOUT = 60


@given("the server is started")
def step_server_started(context):
    """Verify the server is reachable"""
    response = requests.get(f"{context.base_url}/")
    assert response.status_code == 200, f"Server not running at {context.base_url}"


@given("the following promotions")
def step_impl(context):
    """Delete all promotions and load new ones"""

    # Get a list all of the promotions
    rest_endpoint = f"{context.base_url}/api/promotions"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(status.HTTP_200_OK)
    for promotion in context.resp.json():
        context.resp = requests.delete(
            f"{rest_endpoint}/{promotion['id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(status.HTTP_204_NO_CONTENT)

    # load the database with new promotions
    for row in context.table:
        payload = {
            "name": row["name"],
            "promotion_type": row["promotion_type"],
            "discount_value": float(row["discount_value"]),
            "start_date": row["start_date"],
            "end_date": row["end_date"],
        }
        context.resp = requests.post(rest_endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(status.HTTP_201_CREATED)
        context.last_id = context.resp.json()["id"]


@given("there are no promotions")
def step_no_promotions(context):
    """Delete all promotions"""
    rest_endpoint = f"{context.base_url}/api/promotions"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(status.HTTP_200_OK)
    for promotion in context.resp.json():
        context.resp = requests.delete(
            f"{rest_endpoint}/{promotion['id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(status.HTTP_204_NO_CONTENT)


@when('I set the "Promotion ID" to the last created promotion ID')
def step_set_promotion_id(context):
    """Set the Promotion ID field to the last created promotion's ID"""
    element = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.presence_of_element_located((By.ID, "promotion_id"))
    )
    element.clear()
    element.send_keys(str(context.last_id))
