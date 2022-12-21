"""DecentralandAPI tap class."""

from pathlib import Path
from typing import List
from datetime import datetime

from singer_sdk import Tap, Stream
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
from tap_decentraland_api.api_streams import (
    TilesStream,
)

from tap_decentraland_api.snapshot_dao_streams import (
    SnapshotProposalsStream,
    SnapshotVotesStream,
)

from tap_decentraland_api.aragon_dao_streams import (
    AragonProposalsStream,
)

from tap_decentraland_api.coingecko_mana_stream import (
    CoingeckoManaStream,
)

from tap_decentraland_api.scenes_streams import (
    SceneSnapshotStream,
    SceneMappingStream,
    SceneStream,
    SceneChangesStream,
)

from tap_decentraland_api.events_streams import (
    EventsStream
)

STREAM_TYPES = [
    TilesStream,
    SnapshotProposalsStream,
    SnapshotVotesStream,
    AragonProposalsStream,
    CoingeckoManaStream,
    SceneSnapshotStream,
    SceneMappingStream,
    SceneStream,
    EventsStream,
    SceneChangesStream,
]

class TapDecentralandAPI(Tap):
    """DecentralandAPI tap class."""

    name = "tap-decentraland-api"

    config_jsonschema = PropertiesList(
        Property("api_url", StringType, default="https://api.decentraland.org"),
        Property("peer_api_url", StringType, default="https://peer-lb.decentraland.org"),
        Property("scenes_per_run", IntegerType, default=2000),
        Property("governance_snapshot_api_url", StringType, default="https://governance.decentraland.org/api"),
        Property("governance_aragon_api_url", StringType, default="https://api.thegraph.com/subgraphs/name/aragon/aragon-voting-mainnet"),
        Property("coingecko_url", StringType, default="https://api.coingecko.com/api/v3"),
        Property("coingecko_start_date", DateTimeType, default="2017-10-28"),
        Property("catalysts_start_date", DateTimeType, default="2000-01-01"),
        Property("events_api_url", StringType, default="https://events.decentraland.org/api")
    ).to_dict()


    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


# CLI Execution:
cli = TapDecentralandAPI.cli
