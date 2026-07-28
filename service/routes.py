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
Promotion Service with Swagger

Paths:
------
GET  /               - Displays the UI for testing the service
GET  /health          - Health endpoint for Kubernetes probes
GET  /apidocs/        - Displays the Swagger UI for the REST API
GET  /api/promotions      - Returns a list of all Promotions
POST /api/promotions      - Creates a new Promotion
GET  /api/promotions/{id} - Returns the Promotion with the given id
PUT  /api/promotions/{id} - Updates the Promotion with the given id
DELETE /api/promotions/{id} - Deletes the Promotion with the given id
PUT  /api/promotions/{id}/deactivate - Deactivates the Promotion with the given id
DELETE /api/promotions/reset - Resets the database (test use only)
"""

from flask import jsonify, abort, request, make_response
from flask import current_app as app
from flask_restx import Api, Resource, fields, reqparse

from service.models import Promotion, PromotionType, db
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
#
# NOTE: These plain Flask routes must be registered BEFORE the Api
# object below. Flask-RESTX claims the root URL ("/") for its own use
# (redirecting to the Swagger docs) unless a route is already bound to
# it, so our own "/" route has to win the race.
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


@app.route("/health", methods=["GET"])
def health():
    """Health endpoint for Kubernetes probes"""
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Promotion Demo REST API Service",
    description="This is the Promotion Store server implemented with Flask-RESTX.",
    default="promotions",
    default_label="Promotion service operations",
    doc="/apidocs/",
    prefix="/api",
)


######################################################################
# Configure the Swagger models
######################################################################
create_model = api.model(
    "PromotionCreate",
    {
        "name": fields.String(
            required=True,
            description="The name of the Promotion",
            example="Summer Sale",
        ),
        "promotion_type": fields.String(
            required=True,
            enum=[member.name for member in PromotionType],
            description="The type of the Promotion",
            example=PromotionType.PERCENT_OFF.name,
        ),
        # Serialized from a Decimal column, so this travels the wire as a
        # decimal string ("20.00"), not as a JSON number.
        "discount_value": fields.String(
            description="The discount amount or percentage granted by the Promotion",
            example="20.00",
        ),
        "start_date": fields.Date(
            description="The date the Promotion becomes active", example="2026-06-01"
        ),
        "end_date": fields.Date(
            description="The date the Promotion expires", example="2026-06-07"
        ),
        "active": fields.Boolean(
            description="Is the Promotion currently active?", example=True
        ),
    },
)

promotion_model = api.inherit(
    "Promotion",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique id assigned internally by service",
            example=1,
        ),
    },
)

message_model = api.model(
    "Message",
    {
        "message": fields.String(
            description="A human readable status message", example="database reset"
        ),
    },
)

error_model = api.model(
    "Error",
    {
        "status": fields.Integer(description="The HTTP status code", example=404),
        "error": fields.String(
            description="The short name of the error", example="Not Found"
        ),
        "message": fields.String(
            description="A human readable explanation of what went wrong",
            example="Promotion with id '0' was not found.",
        ),
    },
)

# query string arguments for filtering the Promotion list
promotion_args = reqparse.RequestParser()
promotion_args.add_argument(
    "name", type=str, location="args", required=False, help="List Promotions by name"
)
promotion_args.add_argument(
    "promotion_type",
    type=str,
    location="args",
    required=False,
    help="List Promotions by promotion_type",
)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid content type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content type must be {media_type}",
    )


######################################################################
#  PATH: /api/promotions/{id}
######################################################################
@api.route("/promotions/<int:promotion_id>")
@api.param("promotion_id", "The Promotion identifier")
class PromotionResource(Resource):
    """
    PromotionResource class

    Allows the manipulation of a single Promotion
    GET /api/promotions/{id} - Returns a Promotion with the id
    PUT /api/promotions/{id} - Update a Promotion with the id
    DELETE /api/promotions/{id} - Deletes a Promotion with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A PROMOTION
    # ------------------------------------------------------------------
    @api.doc("get_promotions")
    @api.response(200, "Promotion returned", promotion_model)
    @api.response(404, "Promotion not found", error_model)
    def get(self, promotion_id):
        """
        Retrieve a single Promotion

        This endpoint will return a Promotion based on its ID.
        """
        app.logger.info("Request to retrieve Promotion with id: %s", promotion_id)
        promotion = Promotion.find(promotion_id)
        if not promotion:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with id '{promotion_id}' was not found.",
            )

        app.logger.info("Returning Promotion: %s", promotion.name)
        return make_response(jsonify(promotion.serialize()), status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING PROMOTION
    # ------------------------------------------------------------------
    @api.doc("update_promotions")
    @api.response(200, "Promotion updated", promotion_model)
    @api.response(404, "Promotion not found", error_model)
    @api.response(400, "The posted Promotion data was not valid", error_model)
    @api.response(415, "Content-Type was not application/json", error_model)
    @api.expect(promotion_model)
    def put(self, promotion_id):
        """Updates an existing Promotion"""
        app.logger.info("Request to update Promotion with id [%s]", promotion_id)
        check_content_type("application/json")

        promotion = Promotion.find(promotion_id)
        if not promotion:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with id '{promotion_id}' was not found.",
            )

        promotion.deserialize(request.get_json())
        promotion.id = promotion_id  # the URL path id is authoritative
        promotion.update()

        app.logger.info("Promotion with id [%s] updated!", promotion.id)
        return make_response(jsonify(promotion.serialize()), status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # DELETE A PROMOTION
    # ------------------------------------------------------------------
    @api.doc("delete_promotions")
    @api.response(204, "Promotion deleted")
    def delete(self, promotion_id):
        """
        Delete a Promotion

        This endpoint will delete a Promotion based on its ID.
        """
        app.logger.info("Request to delete Promotion with id: %s", promotion_id)
        promotion = Promotion.find(promotion_id)
        if promotion:
            promotion.delete()

        app.logger.info("Promotion with id %s delete complete", promotion_id)
        return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
#  PATH: /api/promotions
######################################################################
@api.route("/promotions", strict_slashes=False)
class PromotionCollection(Resource):
    """Handles all interactions with collections of Promotions"""

    # ------------------------------------------------------------------
    # LIST ALL PROMOTIONS
    # ------------------------------------------------------------------
    @api.doc("list_promotions")
    @api.expect(promotion_args, validate=False)
    @api.response(200, "Promotion list returned", [promotion_model])
    def get(self):
        """Returns a list of all Promotions, optionally filtered by query params"""
        app.logger.info("Request for promotion list")

        args = promotion_args.parse_args()
        name = args["name"]
        promotion_type = args["promotion_type"]

        if name:
            promotions = Promotion.find_by_name(name).all()
        elif promotion_type:
            try:
                promotion_type_enum = PromotionType[promotion_type.upper()]
                promotions = Promotion.find_by_type(promotion_type_enum).all()
            except KeyError:
                promotions = []
        else:
            promotions = Promotion.all()

        results = [promotion.serialize() for promotion in promotions]
        app.logger.info("Returning %d promotions", len(results))

        return make_response(jsonify(results), status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # CREATE A NEW PROMOTION
    # ------------------------------------------------------------------
    @api.doc("create_promotions")
    @api.response(201, "Promotion created", promotion_model)
    @api.response(400, "The posted data was not valid", error_model)
    @api.response(415, "Content-Type was not application/json", error_model)
    @api.expect(create_model)
    def post(self):
        """Create a new Promotion"""
        app.logger.info("Request to create a Promotion")
        check_content_type("application/json")

        promotion = Promotion()
        promotion.deserialize(request.get_json())
        promotion.create()

        location_url = api.url_for(
            PromotionResource, promotion_id=promotion.id, _external=True
        )

        return make_response(
            jsonify(promotion.serialize()),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /api/promotions/{id}/deactivate
######################################################################
@api.route("/promotions/<int:promotion_id>/deactivate")
@api.param("promotion_id", "The Promotion identifier")
class DeactivateResource(Resource):
    """Deactivate action on a Promotion"""

    @api.doc("deactivate_promotions")
    @api.response(200, "Promotion deactivated", promotion_model)
    @api.response(404, "Promotion not found", error_model)
    def put(self, promotion_id):
        """Deactivate a Promotion"""
        app.logger.info("Request to deactivate Promotion with id: %s", promotion_id)

        promotion = Promotion.find(promotion_id)
        if not promotion:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with id '{promotion_id}' was not found.",
            )

        promotion.active = False
        promotion.update()

        app.logger.info("Promotion with id %s has been deactivated", promotion_id)
        return make_response(jsonify(promotion.serialize()), status.HTTP_200_OK)


######################################################################
#  PATH: /api/promotions/reset (test use only)
######################################################################
@api.route("/promotions/reset")
class ResetResource(Resource):
    """Resets the database (test use only)"""

    @api.doc("reset_promotions")
    @api.response(200, "Database reset", message_model)
    def delete(self):
        """Resets the database for testing — should be disabled in production"""
        db.session.query(Promotion).delete()
        db.session.commit()
        return make_response(jsonify(message="database reset"), status.HTTP_200_OK)
