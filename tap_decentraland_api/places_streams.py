"""Places stream class for tap-decentraland-api."""

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
    PropertiesList,
    Property,
    StringType,
)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class PlacesStream(RESTStream):

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
        Property("tags", StringType),
        Property("positions", StringType),
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
        Property("categories", StringType),
        Property("like_rate", NumberType),
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
        row['rowId'] = "|".join([row['id'], row['updated_at']])
        
        if "tags" in row: 
            row['tags'] = ",".join(row['tags'])

        if "positions" in row: 
            row['positions'] = ";".join(row['positions'])

        if "categories" in row: 
            row['categories'] = ",".join(row['categories'])

        return row
    
class WorldsStream(RESTStream):

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

    name = "worlds" 
    path = "/worlds"
    primary_keys = ['rowId']
    replication_key = None  

    schema = PropertiesList(
        Property("rowId", StringType, required=True),
        Property("id", StringType),
        Property("world_name", StringType),
        Property("title", StringType),
        Property("description", StringType),
        Property("image", StringType),
        Property("owner", StringType),
        Property("tags", StringType),
        Property("positions", StringType),
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
        Property("categories", StringType),
        Property("like_rate", NumberType),
        Property("highlighted", BooleanType),
        Property("highlighted_image", StringType),
        Property("featured", BooleanType),
        Property("featured_image", StringType),
        Property("user_favorite", BooleanType),
        Property("user_like", BooleanType),
        Property("user_dislike", BooleanType),
        Property("user_count", IntegerType),
        Property("last_deployed_at", DateTimeType)
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['id'], row['updated_at']])
        
        if "tags" in row: 
            row['tags'] = ",".join(row['tags'])

        if "positions" in row: 
            row['positions'] = ";".join(row['positions'])

        if "categories" in row: 
            row['categories'] = ",".join(row['categories'])

        return row