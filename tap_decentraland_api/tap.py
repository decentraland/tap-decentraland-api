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
from tap_decentraland_api.streams import (
    DecentralandAPIStream,
    TilesStream,
)

STREAM_TYPES = [
    TilesStream,
]


class TapDecentralandAPI(Tap):
    """DecentralandAPI tap class."""

    name = "tap-decentraland-api"

    config_jsonschema = PropertiesList(
        Property("api_url", StringType, default="https://api.decentraland.net"),
    ).to_dict()


    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


# CLI Execution:

cli = TapDecentralandAPI.cli
