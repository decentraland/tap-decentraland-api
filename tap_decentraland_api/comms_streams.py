
"""Stream class for tap-decentraland-api."""


import datetime
from pathlib import Path
from typing import Iterable, Optional
import requests

from singer_sdk.helpers._util import utc_now

from singer_sdk.streams import RESTStream

from singer_sdk import typing as th

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class DecentralandStreamAPIStream(RESTStream):
    """DecentralandAPI stream class."""

    request_timestamp = ""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["peer_api_url"]

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        self.request_timestamp = datetime.datetime.utcnow().isoformat()

        return super().parse_response(response)


class CommsPeersStream(DecentralandStreamAPIStream):
    """Define custom stream."""

    name = "peers"
    path = "/comms/peers"
    primary_keys = ["id"]
    records_jsonpath: str = "$.peers[*]"
    schema = th.PropertiesList(
        th.Property(
            "id",
            th.StringType,
            description="Peer id",
        ),
        th.Property(
            "address",
            th.StringType,
            description="Peer address",
        ),
        th.Property(
            "last_ping",
            th.IntegerType,
            description="Peer last ping in unix timestamp",
        ),
        th.Property("parcel", th.StringType,
                    description="Peer position in world"),
        th.Property("server", th.StringType, description="Peer server"),
        th.Property("time_extracted", th.DateTimeType,
                    description="Request timestamp")
    ).to_dict()

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        if "parcel" in row:
            row['parcel'] = "|".join(str(coord) for coord in row['parcel'])

        row['server'] = self.config.get("peer_api_url")

        row['last_ping'] = row['lastPing']

        row['time_extracted'] = self.request_timestamp

        return row
