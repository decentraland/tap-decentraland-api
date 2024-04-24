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
from tap_decentraland_api.comms_streams import CommsPeersStream

from tap_decentraland_api.events_streams import (
    EventsStream
)

from tap_decentraland_api.places_streams import (
    PlacesStream,
    WorldsStream
)

from tap_decentraland_api.scenes_streams import (
    ContentSnapshotStream,
    SceneChangesStream,
    SceneChangesStreamV2,
    SceneMappingStream,
    SceneStream
)

from tap_decentraland_api.builder_streams import (
    SmartItemsStream,
    TemplatesStream
)

from tap_decentraland_api.snapshot_dao_streams import (
    SnapshotProposalsStream,
    SnapshotVotesStream
)

from tap_decentraland_api.profiles_streams import (
    ProfileChangesStream
)

from tap_decentraland_api.worlds_stream import (
    WorldIndexStream,
    WorldPermissionsStream,
    WorldScenesStream
)


STREAM_TYPES = [
    AragonProposalsStream,
    CoingeckoManaStream,
    EventsStream,
    PlacesStream,
    WorldsStream,
    ContentSnapshotStream,
    SceneMappingStream,
    SceneStream,
    SceneChangesStream,
    SceneChangesStreamV2,
    SnapshotProposalsStream,
    SnapshotVotesStream,
    SmartItemsStream,
    TilesStream,
    ProfileChangesStream,
    CommsPeersStream,
    TemplatesStream,
    WorldIndexStream,
    WorldPermissionsStream,
    WorldScenesStream
]


class TapDecentralandAPI(Tap):
    """DecentralandAPI tap class."""

    name = "tap-decentraland-api"

    config_jsonschema = PropertiesList(
        Property("api_url", StringType,
                 default="https://api.decentraland.org"),
        Property("coingecko_url", StringType,
                 default="https://api.coingecko.com/api/v3"),
        Property("coingecko_start_date", DateTimeType, default="2017-10-28"),
        Property("catalysts_start_date", DateTimeType, default="2000-01-01"),
        Property("events_api_url", StringType,
                 default="https://events.decentraland.org/api"),
        Property("governance_snapshot_api_url", StringType,
                 default="https://governance.decentraland.org/api"),
        Property("governance_aragon_api_url", StringType,
                 default="https://api.thegraph.com/subgraphs/name/aragon/aragon-voting-mainnet"),
        Property("peer_api_url", StringType,
                 default="https://peer-lb.decentraland.org"),
        Property("places_api_url", StringType,
                 default="https://places.decentraland.org/api"),
        Property("scenes_per_run", IntegerType, default=2000),
        Property("builder_api_url", StringType,
                 default="https://builder-api.decentraland.org/v1"),
        Property("sync_content_after", IntegerType,
                 description="Sync content after certain snapshot date in unix timestamp", default=1680998400000),
        Property("world_content_server_url", StringType,
                 description="World content server URL", default="https://worlds-content-server.decentraland.org"),
        Property("builder_assetpacks_url", StringType,
                 description="Builder Asset Packs URL", default="https://builder-assetpacks-prd-bf9fae6.s3.amazonaws.com"),
        Property("profile_stream_max_rows", IntegerType,
                 description="Max rows to fetch from profile changes stream"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


# CLI Execution:
cli = TapDecentralandAPI.cli
