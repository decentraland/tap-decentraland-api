from datetime import datetime
from singer_sdk import PluginBase, RESTStream
from singer_sdk._singerlib import Schema
from singer_sdk.plugin_base import PluginBase as TapBaseClass
from singer_sdk.typing import (
    PropertiesList,
    StringType,
    Property,
    ObjectType,
    ArrayType,
    NumberType,
)
from typing import Any, Dict, Optional, Union, Iterable, cast
import json


class WorldContentServerStream(RESTStream):
    @property
    def url_base(self) -> str:
        return self.config["world_content_server_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snapshot_timestamp = datetime.now().isoformat()


class WorldIndexStream(WorldContentServerStream):
    name = "world_index"
    path = "/index"
    records_jsonpath = "$.data[*]"

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "world_name": record["name"],
        }

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


class WorldPermissionsStream(WorldContentServerStream):
    name = "world_permissions"
    parent_stream_type = WorldIndexStream
    path = "/world"
    primary_keys = ["world_name", "snapshot_at"]

    def get_url(self, context: Optional[dict]) -> str:
        world_name = context["world_name"]
        return super().get_url(context) + f"/{world_name}/permissions"

    def post_process(self, row: Dict, context: Optional[dict]) -> Optional[dict]:
        row['world_name'] = context['world_name']

        row['snapshot_at'] = self.snapshot_timestamp

        return row

    schema = PropertiesList(
        Property("world_name", StringType),
        Property("permissions", ObjectType(
            Property("deployment", ObjectType(
                Property("type", StringType),
                Property("wallets", ArrayType(StringType))
            )),
            Property("access", ObjectType(
                Property("type", StringType),
                Property("wallets", ArrayType(StringType))
            )),
            Property("streaming", ObjectType(
                Property("type", StringType),
                Property("wallets", ArrayType(StringType))
            ))
        )),
        Property('snapshot_at', StringType)
    ).to_dict()


class WorldScenesStream(WorldContentServerStream):
    name = "world_scenes"
    parent_stream_type = WorldIndexStream
    path = "/entities/active"
    rest_method = "POST"
    records_jsonpath = "$[*]"
    primary_keys = ["world_name", "snapshot_at"]

    def prepare_request_payload(self, context: Optional[dict], next_page_token: Optional[Any]) -> Optional[dict]:
        return {
            "pointers": [context["world_name"]],
        }

    def post_process(self, row: dict, context: Optional[dict]) -> Optional[dict]:
        result = {}

        result["scene_hash"] = row.get("id")
        result["world_name"] = context.get("world_name") if context else None
        result["timestamp"] = row.get("timestamp")
        result["version"] = row.get("version")
        result["type"] = row.get("type")
        result["pointers"] = json.dumps(row.get("pointers"))
        result["content"] = json.dumps(row.get("content"))

        metadata = row.get("metadata", {})
        display = metadata.get("display", {})
        contact = metadata.get("contact", {})
        scene = metadata.get("scene", {})
        spawnPoints = metadata.get("spawnPoints", {})
        requiredPermissions = metadata.get("requiredPermissions", {})
        featureToggles = metadata.get("featureToggles", {})
        tags = metadata.get("tags", {})
        worldConfiguration = metadata.get("worldConfiguration", {})
        source = metadata.get("source", {})

        result["title"] = display.get("title")
        result["description"] = display.get("description")
        result["thumbnail"] = display.get("navmapThumbnail")
        result["favicon"] = display.get("favicon")

        result["contact_name"] = contact.get("name")
        result["contact_email"] = contact.get("email")

        result["owner"] = metadata.get("owner")
        result["tiles"] = json.dumps(scene.get("parcels"))
        result["base_tile"] = scene.get("base")

        result["spawn_points"] = json.dumps(spawnPoints)
        result["required_permissions"] = json.dumps(requiredPermissions)
        result["feature_toggles"] = json.dumps(featureToggles)
        result["tags"] = json.dumps(tags)
        result["main"] = metadata.get("main")
        result["world_configuration"] = json.dumps(worldConfiguration)
        result["source"] = json.dumps(source)

        # Remove fields that are already in the schema
        metadata.pop("display", None)
        metadata.pop("contact", None)
        metadata.pop("scene", None)
        metadata.pop("spawnPoints", None)
        metadata.pop("requiredPermissions", None)
        metadata.pop("featureToggles", None)
        metadata.pop("tags", None)
        metadata.pop("worldConfiguration", None)
        metadata.pop("source", None)

        result["metadata"] = json.dumps(metadata)

        result['snapshot_at'] = self.snapshot_timestamp

        return result

    schema = PropertiesList(
        Property("scene_hash", StringType),
        Property("world_name", StringType),
        Property("timestamp", NumberType),
        Property("version", StringType),
        Property("type", StringType),
        Property("pointers", StringType),
        Property("content", StringType),
        # Metadata
        Property("title", StringType),
        Property("description", StringType),
        Property("thumbnail", StringType),
        Property("favicon", StringType),
        Property("contact_name", StringType),
        Property("contact_email", StringType),
        Property("owner", StringType),
        Property("tiles", StringType),
        Property("base_tile", StringType),
        Property("spawn_points", StringType),
        Property("required_permissions", StringType),
        Property("feature_toggles", StringType),
        Property("tags", StringType),
        Property("main", StringType),
        Property("world_configuration", StringType),
        Property("source", StringType),
        Property("metadata", StringType),
        Property('snapshot_at', StringType)
    ).to_dict()
