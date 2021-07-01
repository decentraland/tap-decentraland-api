"""Stream class for tap-decentraland-api."""


import requests, json


from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable


from singer_sdk.streams import RESTStream



from singer_sdk.authenticators import (
    APIAuthenticatorBase,
    SimpleAuthenticator,
    OAuthAuthenticator,
    OAuthJWTAuthenticator
)

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

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class DecentralandStreamAPIStream(RESTStream):
    """DecentralandAPI stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["peer_api_url"]


class SceneSnapshotStream(DecentralandStreamAPIStream):
    name = "scene_snapshot_hash"

    path = "/content/snapshot/scene"

    primary_keys = ['hash']
    replication_method = "INCREMENTAL"
    replication_key = 'lastIncludedDeploymentTimestamp'
    

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "hash": record['hash']
        }


    def parse_response(self, response) -> Iterable[dict]:
        """Parse data"""
        data =response.json()
        yield data


    schema = PropertiesList(
        Property("hash", StringType, required=True),
        Property("lastIncludedDeploymentTimestamp", IntegerType)
    ).to_dict()



class SceneMappingStream(DecentralandStreamAPIStream):
    name = "scene_mapping"

    path = "/content/contents/{hash}"

    primary_keys = ['global_hash', 'scene_hash']
    parent_stream_type = SceneSnapshotStream
    
    def parse_response(self, response) -> Iterable[dict]:
        """Parse data"""

        data =response.json()
        for d in data:
            row = {'scene_hash': d[0], 'parcels': d[1]}
            yield row


    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Add hash"""
        row['global_hash'] = context['hash']
        return row

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "scene_hash": record['scene_hash']
        }

    schema = PropertiesList(
        Property("global_hash", StringType, required=True),
        Property("scene_hash", StringType, required=True),
        Property("parcels", ArrayType(StringType))
    ).to_dict()



class SceneStream(DecentralandStreamAPIStream):

    name = "scene"

    path = "/content/entities/scene"

    primary_keys = ['scene_hash']
    parent_stream_type = SceneMappingStream
    

    def get_url_params(self, partition, next_page_token: Optional[IntegerType] = None) -> dict:
        return {
            "id": partition['scene_hash']
        }

    def parse_response(self, response) -> Iterable[dict]:
        """Parse data"""

        data =response.json()
        for row in data:
            yield row


    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Rename and flatten some fields"""
        row['scene_hash'] = row['id']
        del row['id']

        files_array = [c['file'] for c in row['content']]
        hashes_array = [c['file'] for c in row['content']]

        row['content_files'] = json.dumps(files_array)
        row['content_files_hashes'] = json.dumps(hashes_array)

        # Flatten some properties into json strings
        metadata = row.get('metadata')
        if metadata:
            if 'tags' in metadata:
                row['metadata']['tags'] = json.dumps(metadata['tags'])
            if 'scene' in metadata:
                if 'parcels' in metadata['scene']:
                    row['metadata']['scene']['parcels'] = json.dumps(metadata['scene']['parcels'])
            if 'policy' in metadata:
                if 'blacklist' in metadata['policy']:
                    row['metadata']['policy']['blacklist'] = json.dumps(metadata['policy']['blacklist'])
            if 'requiredPermissions' in metadata:
                row['metadata']['requiredPermissions'] = json.dumps(metadata['requiredPermissions'])
            if 'spawnPoints' in metadata:
                row['metadata']['spawnPoints'] = json.dumps(metadata['spawnPoints'])

        return row

    schema = PropertiesList(
        Property("scene_hash", StringType, required=True),
        Property("type", StringType),
        Property("timestamp", DateTimeType),
        Property("content_files", StringType),
        Property("content_files_hashes", StringType),
        Property("type", StringType),
        Property("metadata", ObjectType(
            Property("display", ObjectType(
                Property("title", StringType),
                Property("favicon", StringType),
                Property("navmapThumbnail", StringType)
            )),
            Property("owner", StringType),
            Property("contact", ObjectType(
                Property("name", StringType),
                Property("email", StringType)
            )),
            Property("main", StringType),
            Property("scene", ObjectType(
                Property("parcels", StringType),
                Property("base", StringType)
            )),
            Property("communications", ObjectType(
                Property("type", StringType),
                Property("signalling", StringType)
            )),
            Property("policy", ObjectType(
                Property("contentRating", StringType),
                Property("fly", BooleanType),
                Property("voiceEnabled", BooleanType),
                Property("blacklist", StringType),
                Property("teleportPosition", StringType)
            )),
            Property("source", ObjectType(
                Property("version", IntegerType),
                Property("origin", StringType),
                Property("projectId", StringType),
                Property("point", ObjectType(
                    Property("x", IntegerType),
                    Property("y", IntegerType)
                )),
                Property("rotation", StringType),
                Property("layout", ObjectType(
                    Property("rows", IntegerType),
                    Property("cols", IntegerType)
                )),
            )),
            Property("requiredPermissions", StringType),
            Property("spawnPoints", StringType),

        )),
        
    ).to_dict()