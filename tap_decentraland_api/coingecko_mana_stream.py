"""Stream class for tap-decentraland-api."""

import backoff
import requests, copy, pendulum, time
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
        if not next_page_token:
            return
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
            if not finished:
                time.sleep(0.2) # Wait 0.2s before next request

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException),
        max_tries=8,
        giveup=lambda e: e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429,
        factor=2,
    )
    def _request_with_backoff(
        self, prepared_request, context: Optional[dict]
    ) -> requests.Response:
        response = self.requests_session.send(prepared_request)
        if self._LOG_REQUEST_METRICS:
            extra_tags = {}
            if self._LOG_REQUEST_METRIC_URLS:
                extra_tags["url"] = cast(str, prepared_request.path_url)
            self._write_request_duration_log(
                endpoint=self.path,
                response=response,
                context=context,
                extra_tags=extra_tags,
            )
        if response.status_code in [401, 403]:
            self.logger.info("Failed request for {}".format(prepared_request.url))
            self.logger.info(
                f"Reason: {response.status_code} - {str(response.content)}"
            )
            raise RuntimeError(
                "Requested resource was unauthorized, forbidden, or not found."
            )
        if response.status_code == 429:
            self.logger.info("Throttled request for {}".format(prepared_request.url))
            raise requests.exceptions.RequestException(
                request=prepared_request,
                response=response
            )
        elif response.status_code >= 400:
            raise RuntimeError(
                f"Error making request to API: {prepared_request.url} "
                f"[{response.status_code} - {str(response.content)}]".replace(
                    "\\n", "\n"
                )
            )

        return response


    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any], context: Optional[dict]
    ) -> Any:
        """Return token identifying next page or None if all records have been read."""
        

        old_token = previous_token or self.get_starting_replication_key_value(context) or self.config["coingecko_start_date"]
        if isinstance(old_token, str):
            old_token = cast(datetime, pendulum.parse(old_token))
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
        context: Optional[dict],
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
        
        row['date'] = row['date'].strftime("%Y-%m-%d")
        return row



    schema = PropertiesList(
        Property("date", StringType, required=True),
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

