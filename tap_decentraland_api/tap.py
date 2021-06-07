"""DecentralandAPI tap class."""

from pathlib import Path
from typing import List

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

STREAM_TYPES = [
    #TilesStream,
    #SnapshotProposalsStream,
    #SnapshotVotesStream,
    AragonProposalsStream
]


class TapDecentralandAPI(Tap):
    """DecentralandAPI tap class."""

    name = "tap-decentraland-api"

    config_jsonschema = PropertiesList(
        Property("api_url", StringType, default="https://api.decentraland.org"),
        Property("governance_snapshot_api_url", StringType, default="https://governance.decentraland.org/api"),
        Property("governance_aragon_api_url", StringType, default="https://api.thegraph.com/subgraphs/name/aragon/aragon-voting-mainnet"),
    ).to_dict()


    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


# CLI Execution:

cli = TapDecentralandAPI.cli
