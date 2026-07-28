######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
TestPromotion API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.common import status
from service.models import db, Promotion, PromotionType
from tests.factories import PromotionFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/promotions"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Promotion).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page and return HTML"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b"Promotions Service", resp.data)

    def test_health_endpoint(self):
        """It should return OK when the service is healthy"""
        resp = self.client.get("/health")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), {"status": "OK"})

    def test_swagger_ui(self):
        """It should display the Swagger UI at /apidocs/"""
        resp = self.client.get("/apidocs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(b"swagger", resp.data.lower())

    def test_swagger_spec_documents_models(self):
        """It should publish a Swagger spec with the API under /api"""
        resp = self.client.get("/api/swagger.json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        spec = resp.get_json()
        self.assertIn("/promotions", spec["paths"])
        self.assertEqual(spec["basePath"], "/api")

        for model in ("Promotion", "PromotionCreate", "Error", "Message"):
            self.assertIn(model, spec["definitions"])

    def test_swagger_spec_documents_payloads(self):
        """It should document request and response payloads with models"""
        spec = self.client.get("/api/swagger.json").get_json()

        # the request body of a POST is documented by the PromotionCreate model
        post = spec["paths"]["/promotions"]["post"]
        body = [p for p in post["parameters"] if p["in"] == "body"][0]
        self.assertEqual(body["schema"]["$ref"], "#/definitions/PromotionCreate")

        # a 201 returns a single Promotion, a 200 list returns an array of them
        self.assertEqual(
            post["responses"]["201"]["schema"]["$ref"], "#/definitions/Promotion"
        )
        list_schema = spec["paths"]["/promotions"]["get"]["responses"]["200"]["schema"]
        self.assertEqual(list_schema["type"], "array")
        self.assertEqual(list_schema["items"]["$ref"], "#/definitions/Promotion")

        # error payloads are documented too
        get_by_id = spec["paths"]["/promotions/{promotion_id}"]["get"]
        self.assertEqual(
            get_by_id["responses"]["404"]["schema"]["$ref"], "#/definitions/Error"
        )

    def test_create_promotion(self):
        """It should create a promotion and return 201 with a Location header"""
        promotion = PromotionFactory()
        payload = promotion.serialize()
        payload.pop("id")  # id is assigned by the DB, not provided by the client

        resp = self.client.post(
            BASE_URL,
            json=payload,
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("Location", resp.headers)

        data = resp.get_json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["name"], payload["name"])
        self.assertEqual(data["promotion_type"], payload["promotion_type"])
        self.assertEqual(data["discount_value"], str(payload["discount_value"]))
        self.assertEqual(data["start_date"], payload["start_date"])
        self.assertEqual(data["end_date"], payload["end_date"])

        # verify location header is fully qualifie URL
        location = resp.headers["Location"]
        self.assertTrue(location.startswith("http://"))
        self.assertTrue(location.endswith(f"/promotions/{data['id']}"))

        # verify location header actually resolves to the created promo
        follow_resp = self.client.get(location.replace("http://localhost", ""))
        self.assertEqual(follow_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(follow_resp.get_json()["id"], data["id"])

    def test_create_promotion_invalid_content_type(self):
        """It should return 415 when Content-Type is not application/json"""
        resp = self.client.post(
            BASE_URL,
            data="not json",
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_promotion_missing_required_field(self):
        """It should return 400 when required fields are missing"""
        resp = self.client.post(
            BASE_URL,
            json={"discount_value": 10.0},  # missing name and promotion_type
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_invalid_promotion_type(self):
        """It should return 400 when promotion_type is not a valid enum value"""
        resp = self.client.post(
            BASE_URL,
            json={
                "name": "Bad Type Promo",
                "promotion_type": "INVALID_TYPE",
                "discount_value": 5.0,
            },
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_promotion(self):
        """It should delete a Promotion"""
        promotion = PromotionFactory()
        promotion.create()

        resp = self.client.delete(f"{BASE_URL}/{promotion.id}")

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")
        self.assertIsNone(Promotion.find(promotion.id))

    def test_delete_promotion_not_found(self):
        """It should return no content when deleting a missing Promotion"""
        resp = self.client.delete(f"{BASE_URL}/0")

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")

    def test_read_promotion(self):
        """It should read a single Promotion"""
        promotion = PromotionFactory()
        promotion.create()

        resp = self.client.get(f"{BASE_URL}/{promotion.id}")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], promotion.id)
        self.assertEqual(data["name"], promotion.name)
        self.assertEqual(data["promotion_type"], promotion.promotion_type.name)
        self.assertEqual(data["start_date"], promotion.start_date.isoformat())
        self.assertEqual(data["end_date"], promotion.end_date.isoformat())

    def test_read_promotion_not_found(self):
        """It should not read a Promotion that does not exist"""
        resp = self.client.get(f"{BASE_URL}/0")

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(data["error"], "Not Found")

    def test_get_promotion_list(self):
        """It should return a list of all Promotions"""
        promotions = PromotionFactory.create_batch(5)
        for promotion in promotions:
            promotion.create()

        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_get_promotion_list_when_empty(self):
        """It should return an empty list when no Promotions exist"""
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data, [])

    def test_get_promotion_list_returns_correct_fields(self):
        """It should return Promotions with all expected fields"""
        promotion = PromotionFactory()
        promotion.create()

        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)

        result = data[0]
        self.assertEqual(result["name"], promotion.name)
        self.assertEqual(result["promotion_type"], promotion.promotion_type.name)
        self.assertEqual(
            float(result["discount_value"]), float(promotion.discount_value)
        )
        self.assertEqual(result["start_date"], promotion.start_date.isoformat())
        self.assertEqual(result["end_date"], promotion.end_date.isoformat())
        self.assertIn("id", result)

    def test_update_promotion(self):
        """It should update an existing Promotion"""
        promotion = PromotionFactory()
        promotion.create()

        new_data = promotion.serialize()
        new_data["name"] = "Updated Promo Name"
        new_data["discount_value"] = "25.00"
        new_data["end_date"] = "2026-12-31"

        resp = self.client.put(
            f"{BASE_URL}/{promotion.id}",
            json=new_data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(data["id"], promotion.id)
        self.assertEqual(data["name"], "Updated Promo Name")
        self.assertEqual(float(data["discount_value"]), 25.00)
        self.assertEqual(data["end_date"], "2026-12-31")

    def test_update_promotion_persists_to_database(self):
        """It should persist the updated fields after a PUT"""
        promotion = PromotionFactory()
        promotion.create()

        new_data = promotion.serialize()
        new_data["name"] = "Persisted Name"

        resp = self.client.put(
            f"{BASE_URL}/{promotion.id}",
            json=new_data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(f"{BASE_URL}/{promotion.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["name"], "Persisted Name")

    def test_update_promotion_not_found(self):
        """It should return 404 when updating a Promotion that does not exist"""
        promotion = PromotionFactory()
        new_data = promotion.serialize()
        new_data.pop("id")

        resp = self.client.put(
            f"{BASE_URL}/0",
            json=new_data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        data = resp.get_json()
        self.assertIn("status", data)
        self.assertIn("error", data)
        self.assertIn("message", data)
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(data["error"], "Not Found")

    def test_update_promotion_missing_required_field(self):
        """It should return 400 when the update payload is missing required fields"""
        promotion = PromotionFactory()
        promotion.create()

        resp = self.client.put(
            f"{BASE_URL}/{promotion.id}",
            json={"discount_value": "10.00"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_promotion_invalid_content_type(self):
        """It should return 415 when Content-Type is not application/json"""
        promotion = PromotionFactory()
        promotion.create()

        resp = self.client.put(
            f"{BASE_URL}/{promotion.id}",
            data="not json",
            content_type="text/plain",
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_promotion_does_not_change_id(self):
        """It should not allow the promotion id to be changed via the payload"""
        promotion = PromotionFactory()
        promotion.create()
        original_id = promotion.id

        new_data = promotion.serialize()
        new_data["id"] = original_id + 9999

        resp = self.client.put(
            f"{BASE_URL}/{original_id}",
            json=new_data,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["id"], original_id)

    def test_method_not_allowed(self):
        """It should return 405 when an unsupported HTTP method is used"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertIn("status", data)
        self.assertIn("error", data)
        self.assertIn("message", data)
        self.assertEqual(data["status"], status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(data["error"], "Method not Allowed")

    def test_internal_server_error(self):
        """It should return 500 when an unexpected error occurs"""
        app.config["PROPAGATE_EXCEPTIONS"] = False
        try:
            with patch(
                "service.routes.Promotion.all", side_effect=Exception("boom")
            ):
                resp = self.client.get(BASE_URL)
            self.assertEqual(
                resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            data = resp.get_json()
            self.assertIn("status", data)
            self.assertIn("error", data)
            self.assertIn("message", data)
            self.assertEqual(
                data["status"], status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertEqual(data["error"], "Internal Server Error")
        finally:
            app.config["PROPAGATE_EXCEPTIONS"] = True

    def test_list_promotions_filtered_by_type(self):
        """It should filter promotions by promotion_type"""
        PromotionFactory(promotion_type=PromotionType.BOGO).create()
        PromotionFactory(promotion_type=PromotionType.BOGO).create()
        PromotionFactory(promotion_type=PromotionType.PERCENT_OFF).create()

        resp = self.client.get(BASE_URL, query_string={"promotion_type": "BOGO"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)
        for promo in data:
            self.assertEqual(promo["promotion_type"], "BOGO")

    def test_list_promotions_filtered_by_name(self):
        """It should filter promotions by name"""
        PromotionFactory(name="Big Sale").create()
        PromotionFactory(name="Other Sale").create()

        resp = self.client.get(BASE_URL, query_string={"name": "Big Sale"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Big Sale")

    def test_list_promotions_filtered_by_unknown_type_returns_empty(self):
        """It should return 200 and an empty list for a nonexistent promotion_type"""
        PromotionFactory(promotion_type=PromotionType.BOGO).create()

        resp = self.client.get(BASE_URL, query_string={"promotion_type": "Expired"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data, [])

    def test_list_promotions_no_filter_returns_all(self):
        """It should return all promotions when no query params are given"""
        PromotionFactory.create_batch(3)
        for p in PromotionFactory.create_batch(3):
            p.create()

        resp = self.client.get(BASE_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 3)

    def test_deactivate_promotion(self):
        """It should deactivate an active promotion and return 200 with active: False"""
        promotion = PromotionFactory(active=True)
        promotion.create()

        resp = self.client.put(f"{BASE_URL}/{promotion.id}/deactivate")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], promotion.id)
        self.assertFalse(data["active"])

    def test_deactivate_already_inactive_promotion(self):
        """It should return 200 and keep active: False when promotion is already inactive"""
        promotion = PromotionFactory(active=False)
        promotion.create()

        resp = self.client.put(f"{BASE_URL}/{promotion.id}/deactivate")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertFalse(data["active"])

    def test_deactivate_promotion_not_found(self):
        """It should return 404 when the promotion does not exist"""
        resp = self.client.put(f"{BASE_URL}/0/deactivate")

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertEqual(data["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(data["error"], "Not Found")

    def test_deactivate_promotion_persists(self):
        """It should persist the deactivated state when re-fetched"""
        promotion = PromotionFactory(active=True)
        promotion.create()

        self.client.put(f"{BASE_URL}/{promotion.id}/deactivate")

        resp = self.client.get(f"{BASE_URL}/{promotion.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.get_json()["active"])

    def test_reset_promotions(self):
        """It should delete all Promotions and return 200"""
        promotions = PromotionFactory.create_batch(5)
        for promotion in promotions:
            promotion.create()

        resp = self.client.delete(f"{BASE_URL}/reset")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json(), [])
