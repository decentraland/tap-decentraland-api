"""Stream class for tap-decentraland-api."""


import requests, copy, pendulum
from datetime import datetime, date, timedelta

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
    cast
)

def escape_backslashes(variable):
    if isinstance(variable, str):
        return variable.replace('\\', '\\\\')

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class CoingeckoTokenStream(RESTStream):

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["coingecko_url"]


    def parse_response(self, response, next_page_token) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()
        resp_json['date'] = next_page_token
        yield resp_json #Only one row per query

    def request_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Request records from REST endpoint(s), returning response records.

        If pagination is detected, pages will be recursed automatically.
        """
        next_page_token: Any = self.get_next_page_token(None, None, context)
        finished = False
        while not finished:
            prepared_request = self.prepare_request(
                context, next_page_token=next_page_token
            )
            resp = self._request_with_backoff(prepared_request, context)
            for row in self.parse_response(resp, next_page_token):
                yield row
            previous_token = copy.deepcopy(next_page_token)
            next_page_token = self.get_next_page_token(
                response=resp, previous_token=previous_token, context=context
            )
            if next_page_token and next_page_token == previous_token:
                raise RuntimeError(
                    f"Loop detected in pagination. "
                    f"Pagination token {next_page_token} is identical to prior token."
                )
            # Cycle until get_next_page_token() no longer returns a value
            finished = not next_page_token

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any], context: Optional[dict]
    ) -> Any:
        """Return token identifying next page or None if all records have been read."""
        

        old_token = previous_token or self.get_starting_replication_key_value(context) or cast(datetime, pendulum.parse(self.config["coingecko_start_date"]))
        signpost = self.get_replication_key_signpost(context)
        
        if old_token < signpost:
            next_page_token = old_token + timedelta(days=1)
            self.logger.info(f"Next page: {next_page_token}")
            return next_page_token
        else:
            return None


class CoingeckoManaStream(CoingeckoTokenStream):
    name = "coingecko_mana_token"

    path = "/coins/decentraland/history"

    primary_keys = ['date']
    replication_key = 'date'
    replication_method = "INCREMENTAL"
    is_sorted = True

    def get_url_params(
        self,
        partition: Optional[dict],
        next_page_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        return {"date": next_page_token.strftime('%d-%m-%Y'), "localization": "false"}
       

    def get_replication_key_signpost(
        self, context: Optional[dict]
    ) -> Optional[Union[datetime, Any]]:
        return cast(datetime, pendulum.yesterday(tz='UTC'))

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        market_data = row.get('market_data')
        if market_data:
            row['price_usd'] = market_data.get('current_price').get('usd')
            row['market_cap_usd'] = market_data.get('market_cap').get('usd')
            row['total_volume_usd'] = market_data.get('total_volume').get('usd')
        return row



    schema = PropertiesList(
        Property("date", DateTimeType, required=True),
        Property("price_usd", NumberType),
        Property("market_cap_usd", NumberType),
        Property("total_volume_usd", NumberType),
        Property("community_data", ObjectType(
            Property("twitter_followers", NumberType),
            Property("reddit_average_posts_48h", NumberType),
            Property("reddit_average_comments_48h", NumberType),
            Property("reddit_subscribers", NumberType),
            Property("reddit_accounts_active_48h", StringType),
        )),
        Property("public_interest_stats", ObjectType(
            Property("alexa_rank", NumberType),
        ))
    ).to_dict()

