"""Stream class for tap-decentraland-api."""

from datetime import datetime, timedelta
import json


from pathlib import Path
from typing import Any, Dict, Optional, Union
from singer_sdk.helpers._util import utc_now

from singer_sdk.streams import RESTStream

from singer_sdk.typing import (
    IntegerType,
    PropertiesList,
    Property,
    StringType,
)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class DecentralandStreamAPIStream(RESTStream):
    """DecentralandAPI stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["peer_api_url"]


class ProfileChangesStream(DecentralandStreamAPIStream):

    name = "profile_changes"

    path = "/content/pointer-changes"

    primary_keys = ['profile_hash']
    replication_method = "INCREMENTAL"
    replication_key = "entityTimestamp"
    is_sorted = True
    records_jsonpath: str = "$.deltas[*]"
    next_page_token_jsonpath: str = "$.deltas[-1:].entityTimestamp"
    RESULTS_PER_PAGE = 500
    last_id = None

    def get_url_params(
        self,
        context: Optional[dict],
        next_page_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        next_timestamp = datetime.strptime(
            self.config["catalysts_start_date"], "%Y-%m-%d").timestamp() * 1000
        replication_key_value = self.get_starting_replication_key_value(
            context)
        signpost = self.get_replication_key_signpost(context)

        if next_page_token:
            next_timestamp = next_page_token
        elif replication_key_value:
            next_timestamp = replication_key_value

        return {
            "limit": self.RESULTS_PER_PAGE,
            "from": next_timestamp,
            "to": signpost,
            "sortingOrder": "ASC",
            "sortingField": "entity_timestamp",
            "entityType": "profile",
            "lastId": self.last_id
        }

    def get_replication_key_signpost(
        self, context: Optional[dict]
    ) -> Optional[Union[datetime, Any]]:
        one_day_ago = utc_now() - timedelta(hours=24)
        return int(one_day_ago.timestamp() * 1000)

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Rename and flatten some fields"""
        row['profile_hash'] = row['entityId']
        self.last_id = row['profile_hash']
        del row['entityId']

        row['entity_timestamp'] = int(row['entityTimestamp'])
        row['local_timestamp'] = int(row['localTimestamp'])
        row['wallet_id'] = row['pointers'][0].lower()  # This is the user address.

        if row['metadata']:
            row['name'] = row['metadata']['avatars'][0].get(
                'name') if 'name' in row['metadata']['avatars'][0] else ""
            row['description'] = row['metadata']['avatars'][0].get(
                'description') if 'description' in row['metadata']['avatars'][0] else ""
            row['avatar'] = json.dumps(row['metadata']['avatars'][0]['avatar'])

        row['deployer_address'] = row['deployerAddress'].lower()
        row['version'] = row['version']
        row['deployment_id'] = row['deploymentId']

        return row

    schema = PropertiesList(
        Property("profile_hash", StringType, required=True),
        Property("entity_timestamp", IntegerType),
        Property("local_timestamp", IntegerType),
        Property("wallet_id", StringType),
        Property("name", StringType),
        Property("description", StringType),
        Property("avatar", StringType),
        Property("deployer_address", StringType),
        Property("version", StringType),
    ).to_dict()
