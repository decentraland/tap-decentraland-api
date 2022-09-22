"""Events stream class for tap-decentraland-api."""

import logging, json
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

class SmartItemsStream(RESTStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["smart_items_api_url"]

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

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['id'],row['updated_at']])

        # Flatten some properties into json strings
        assets = row.get('assets')
        if assets:
            if 'id' in assets:
                row['assets']['id'] = json.dumps(assets['id'])
            if 'asset_pack_id' in assets:
                row['assets']['asset_pack_id'] = json.dumps(assets['asset_pack_id'])
            

        return row

    name = "smart_items"
    path = "/assetPacks"
    primary_keys = ['rowId']
    replication_key = None  
    
    schema = PropertiesList(
        Property("rowId", StringType, required=True),
        Property("id", StringType),
        Property("title", StringType),
        Property("thumbnail", StringType),
        Property("created_at", DateTimeType),
        Property("updated_at", DateTimeType),
        Property("eth_address", StringType),
        Property("assets", ObjectType(
            Property("id", StringType),
            Property("asset_pack_id", StringType),
            Property("name", StringType),
            Property("model", StringType),
            Property("thumbnail", StringType),
            Property("tags", ArrayType),
            Property("category", StringType),
            Property("created_at", DateTimeType),
            Property("updated_at", DateTimeType),
            Property("metrics", ObjectType(
                Property("pebbles.glb", StringType))),
            Property("created_at", DateTimeType),
            Property("updated_at", DateTimeType),            
            Property("metrics", ObjectType(
                Property("triangles", IntegerType),
                Property("materials", IntegerType),
                Property("textures", IntegerType),
                Property("meshes", IntegerType),
                Property("bodies", IntegerType),
                Property("entities", IntegerType))),
            Property("script", StringType),
            Property("parameters", ArrayType),
            Property("actions", ArrayType),
            Property("legacy_id", StringType))
            )
    ).to_dict()