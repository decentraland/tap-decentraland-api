"""DecentralandAPI tap class."""

from pathlib import Path
from typing import List
from datetime import datetime

from singer_sdk import Tap, Stream
from singer_sdk.typing import (
    DateTimeType,
    IntegerType,
    PropertiesList,
    Property,
    StringType
)

from tap_decentraland_api.api_streams import (
    TilesStream
)

from tap_decentraland_api.aragon_dao_streams import (
    AragonProposalsStream
)

from tap_decentraland_api.coingecko_mana_stream import (
    CoingeckoManaStream
)

from tap_decentraland_api.events_streams import (
    EventsStream
)

from tap_decentraland_api.places_streams import (
    PlacesStream
)

from tap_decentraland_api.scenes_streams import (
    SceneChangesStream,
    SceneMappingStream,
    SceneSnapshotStream,
    SceneStream
)

from tap_decentraland_api.smart_items_streams import (
    SmartItemsStream
)

from tap_decentraland_api.snapshot_dao_streams import (
    SnapshotProposalsStream,
    SnapshotVotesStream
)

STREAM_TYPES = [
    AragonProposalsStream,
    CoingeckoManaStream,
    EventsStream,
    PlacesStream,
    SceneChangesStream,
    SceneMappingStream,
    SceneSnapshotStream,
    SceneStream,
    SnapshotProposalsStream,
    SnapshotVotesStream,
    SmartItemsStream,
    TilesStream
]

class TapDecentralandAPI(Tap):
    """DecentralandAPI tap class."""

    name = "tap-decentraland-api"

    config_jsonschema = PropertiesList(
        Property("api_url", StringType, default="https://api.decentraland.org"),
        Property("coingecko_url", StringType, default="https://api.coingecko.com/api/v3"),
        Property("coingecko_start_date", DateTimeType, default="2017-10-28"),
        Property("events_api_url", StringType, default="https://events.decentraland.org/api"),
        Property("governance_snapshot_api_url", StringType, default="https://governance.decentraland.org/api"),
        Property("governance_aragon_api_url", StringType, default="https://api.thegraph.com/subgraphs/name/aragon/aragon-voting-mainnet"),
        Property("peer_api_url", StringType, default="https://peer-lb.decentraland.org"),
        Property("places_api_url", StringType, default="https://places.decentraland.org/api"),
        Property("scenes_per_run", IntegerType, default=2000),
        Property("smart_items_url", StringType, default="https://builder-api.decentraland.org/v1"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]

# CLI Execution:
cli = TapDecentralandAPI.cli
