"""Stream class for tap-decentraland-api."""


import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable
from singer_sdk.streams import RESTStream



from singer_sdk.authenticators import (
    APIAuthenticatorBase,
    SimpleAuthenticator,
    OAuthAuthenticator,
    OAuthJWTAuthenticator
)

from singer_sdk.typing import (
    ArrayType,
    BooleanType,
    DateTimeType,
    IntegerType,
    NumberType,
    ObjectType,
    PropertiesList,
    Property,
    StringType,
)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class DecentralandAPIStream(RESTStream):
    """DecentralandAPI stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["api_url"]


class EventsStream(DecentralandAPIStream):
    name = "events"

    path = "/api/events"

    primary_keys = ['id']
    replication_key = None
    
    schema = PropertiesList(
        Property("id", StringType, required=True),
        Property("name", StringType),
        Property("description", StringType),
        Property("approved", BooleanType),
        Property("rejected", BooleanType),
        Property("highlighted", BooleanType),
        Property("trending", BooleanType),
        # Property("image", ?URIType),
        Property("user", BooleanType),
        Property("user_name", BooleanType),
        Property("total_attendees", BooleanType),
        Property("latest_attendees", BooleanType),
        Property("url", BooleanType),
        Property("scene_name", BooleanType),
        Property("start_at", BooleanType),
        Property("finish_at", BooleanType),
        Property("next_start_at", BooleanType),
        Property("next_finish_at", BooleanType),
        Property("all_day", BooleanType),
        Property("recurrent", BooleanType),
        Property("recurrent_frequency", BooleanType),
        Property("recurrent_setpos", BooleanType),
        Property("recurrent_setpos", BooleanType),
        Property("recurrent_monthday", BooleanType),
        Property("recurrent_weekday_mask", BooleanType),
        Property("recurrent_month_mask", BooleanType),
        Property("recurrent_interval", BooleanType),
        Property("recurrent_count", BooleanType),
        Property("recurrent_until", BooleanType),
        Property("created_at", BooleanType),
        Property("updated_at", BooleanType),
        Property("price", NumberType),
    ).to_dict()


    def parse_response(self, response) -> Iterable[dict]:
        """Parse Tiles rows"""

        data =response.json().get("data")
        for _, t in data.items():
            yield t
