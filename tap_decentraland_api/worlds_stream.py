from singer_sdk import RESTStream
from singer_sdk.typing import (
    PropertiesList,
    StringType,
    Property,
    ObjectType,
    ArrayType,
    NumberType,
)


class WorldContentServerStream(RESTStream):
    @property
    def url_base(self) -> str:
        return self.config["world_content_server_url"]


class WorldIndexStream(WorldContentServerStream):
    name = "world_index"
    path = "/index"
    records_jsonpath = "$.data[*]"

    schema = PropertiesList(
        Property("name", StringType),
        Property("scenes", ArrayType(ObjectType(
            Property("id", StringType),
            Property("title", StringType),
            Property("description", StringType),
            Property("thumbnail", StringType),
            Property("pointers", ArrayType(StringType)),
            Property("timestamp", NumberType),
        )))
    ).to_dict()
