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

    # Alternatively, use a static string for url_base:
    # url_base = "https://api.mysample.com"


    def get_url_params(
        self,
        partition: Optional[dict],
        next_page_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization.

        If paging is supported, developers may override this method with specific paging
        logic.
        """
        params = {}
        starting_datetime = self.get_starting_timestamp(partition)
        if starting_datetime:
            params["updated"] = starting_datetime
        return params

class TilesStream(DecentralandAPIStream):
    name = "tiles"

    path = "/v2/tiles"

    primary_keys = ['id']
    replication_key = None
    
    schema = PropertiesList(
        Property("id", StringType, required=True),
        Property("name", StringType),
        Property("type", StringType),
        Property("x", IntegerType),
        Property("y", IntegerType),
        Property("updatedAt", IntegerType),
        Property("top", BooleanType),
        Property("left", BooleanType),
        Property("topLeft", BooleanType),
        Property("estateId", StringType),
        Property("owner", StringType),
        Property("tokenId", StringType),
        Property("price", NumberType),
    ).to_dict()


    def parse_response(self, response) -> Iterable[dict]:
        """Parse Tiles rows"""

        data =response.json().get("data")
        for _, t in data.items():
            yield t
