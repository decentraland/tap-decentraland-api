"""Events stream class for tap-decentraland-api."""

import logging
import requests
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable
from singer_sdk.streams import RESTStream

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

class PlacesStream(RESTStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["places_api_url"]

    def parse_response(self, response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        data = response.json().get("data")
        try:
            for row in data:                
                yield row
        except Exception as err:
            self.logger.warn(f"(stream: {self.name}) Problem with response: {data}")
            raise err

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Any:
        """Return token identifying next page or None if all records have been read."""
        
        data = response.json().get("data")
        results_len = len(data)

        old_token = previous_token or 0
        self.logger.info(f"Old token: {old_token}")
        self.logger.info(f"Results: {results_len}")
        
        if results_len == self.RESULTS_PER_PAGE:
            next_page_token = old_token + self.RESULTS_PER_PAGE
            self.logger.info(f"Next page: {next_page_token}")
            return next_page_token
        else:
            self.logger.info(f"No more pages")
            return None # Finished if we have less than RESULTS_PER_PAGE

    def get_url_params(
        self,
        context: Optional[dict],
        next_page_token: Optional[Any] = None,
        list = "all"
    ) -> Dict[str, Any]:
        offset = 0
        if next_page_token:
            offset = next_page_token
        self.logger.info(f"Offset: {offset}")
        return {"limit": self.RESULTS_PER_PAGE, "offset": offset, "list":list}

    name = "places" 
    path = "/places"
    primary_keys = ['rowId']
    replication_key = None  
    
    schema = PropertiesList(
        Property("rowId", StringType, required=True),
        Property("id", StringType),
        Property("title", StringType),
        Property("description", StringType),
        Property("image", StringType),
        Property("owner", StringType),
        Property("tags", ArrayType),
        Property("positions", ArrayType),
        Property("base_position", StringType),
        Property("contact_name", StringType),
        Property("contact_email", StringType),
        Property("content_rating", StringType),
        Property("disabled", BooleanType),
        Property("disabled_at", DateTimeType),
        Property("created_at", DateTimeType),
        Property("updated_at", DateTimeType),
        Property("favorites", IntegerType),
        Property("likes", IntegerType),
        Property("dislikes", IntegerType),
        Property("categories", ArrayType),
        Property("like_rate", IntegerType),
        Property("highlighted", BooleanType),
        Property("highlighted_image", StringType),
        Property("featured", BooleanType),
        Property("featured_image", StringType),
        Property("user_favorite", BooleanType),
        Property("user_like", BooleanType),
        Property("user_dislike", BooleanType),
        Property("user_count", IntegerType),
        Property("user_visits", IntegerType),
        Property("last_deployed_at", DateTimeType)
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['id'],row['updated_at']])
        
        return row