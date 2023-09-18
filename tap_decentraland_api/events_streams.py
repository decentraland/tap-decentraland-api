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

class EventsStream(RESTStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["events_api_url"]

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

    name = "events"
    path = "/events"
    primary_keys = ['rowId']
    replication_key = None  
    
    schema = PropertiesList(
        Property("rowId", StringType, required=True),
        Property("id", StringType),
        Property("name", StringType),
        Property("description", StringType),
        Property("approved", BooleanType),
        Property("rejected", BooleanType),
        Property("highlighted", BooleanType),
        Property("trending", BooleanType),
        Property("user", StringType),
        Property("user_name", StringType),
        Property("total_attendees", IntegerType),
        Property("url", StringType),
        Property("scene_name", StringType),
        Property("start_at", DateTimeType),
        Property("finish_at", DateTimeType),
        Property("next_start_at", DateTimeType),
        Property("next_finish_at", DateTimeType),
        Property("all_day", BooleanType),
        Property("recurrent", BooleanType),
        Property("recurrent_frequency", StringType),
        Property("recurrent_setpos", IntegerType),
        Property("recurrent_monthday", IntegerType),
        Property("recurrent_weekday_mask", IntegerType),
        Property("recurrent_month_mask", IntegerType),
        Property("recurrent_interval", IntegerType),
        Property("recurrent_count", IntegerType),
        Property("recurrent_until", DateTimeType),
        Property("created_at", DateTimeType),
        Property("updated_at", DateTimeType),
        Property("tile_x", IntegerType),
        Property("tile_y", IntegerType),
        Property("world", BooleanType)
    ).to_dict()


    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['id'],row['updated_at']])
        
        position = row.get('position')
        if position and len(position) >= 2:
            row['tile_x'] = int(position[0])
            row['tile_y'] = int(position[1])

        return row