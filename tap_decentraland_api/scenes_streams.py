"""Stream class for tap-decentraland-api."""

from datetime import datetime, timedelta
import requests
import json
import backoff

from pathlib import Path
from typing import Any, Dict, Optional, Union, Iterable, cast
from singer_sdk.helpers._util import utc_now

from singer_sdk.streams import RESTStream

from singer_sdk.typing import (
    ArrayType,
    BooleanType,
    IntegerType,
    ObjectType,
    PropertiesList,
    Property,
    StringType,
)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


def processSceneMetadata(metadata):
    if 'tags' in metadata:
        metadata['tags'] = json.dumps(metadata['tags'])

    if 'scene' in metadata:
        # These are dumped as json
        if 'parcels' in metadata['scene']:
            metadata['scene']['parcels'] = json.dumps(
                metadata['scene']['parcels'])
        if 'base' in metadata['scene']:
            metadata['scene']['base'] = json.dumps(metadata['scene']['base'])

    if 'policy' in metadata and metadata['policy'] is not None:
        # Blacklist dumped as json
        if 'blacklist' in metadata['policy']:
            metadata['policy']['blacklist'] = json.dumps(
                metadata['policy']['blacklist'])

        # Fly should be boolean, but can be string
        if 'fly' in metadata['policy'] and isinstance(metadata['policy']['fly'], str):
            metadata['policy']['fly'] = metadata['policy']['fly'].lower() == 'true'

        # voiceEnabled should be boolean, but can be string
        if 'voiceEnabled' in metadata['policy'] and isinstance(metadata['policy']['voiceEnabled'], str):
            metadata['policy']['voiceEnabled'] = metadata['policy']['voiceEnabled'].lower(
            ) == 'true'
        # teleportPosition should be string, but can be boolean
        if 'teleportPosition' in metadata['policy'] and not isinstance(metadata['policy']['teleportPosition'], str):
            metadata['policy']['teleportPosition'] = str(
                metadata['policy']['teleportPosition'])

    # These are dumped as json
    if 'requiredPermissions' in metadata:
        metadata['requiredPermissions'] = json.dumps(
            metadata['requiredPermissions'])
    if 'spawnPoints' in metadata:
        metadata['spawnPoints'] = json.dumps(metadata['spawnPoints'])
    if 'tags' in metadata:
        metadata['tags'] = json.dumps(metadata['tags'])
    if 'source' in metadata:
        metadata['source'] = json.dumps(metadata['source'])

    return metadata


class DecentralandStreamAPIStream(RESTStream):
    """DecentralandAPI stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["peer_api_url"]


class ContentSnapshotStream(DecentralandStreamAPIStream):
    name = "content_snapshot"
    path = "/content/snapshots"
    record_jsonpath = "$[*]"
    primary_keys = ["hash"]
    replication_key = "init_timestamp"
    replication_method = "INCREMENTAL"

    def parse_response(self, response) -> Iterable[Dict]:
        """Parse data"""
        data = response.json()

        for snapshot in data:
            # Avoid syncing snapshots before a certain date.
            syncAfter = self.config['sync_content_after']

            if syncAfter is not None:
                if snapshot['timeRange']['initTimestamp'] < syncAfter:
                    self.logger.warn(
                        'Hash %s is before sync date %s, skipping', snapshot['hash'], syncAfter)
                    continue

            yield {
                "hash": snapshot['hash'],
                "init_timestamp": snapshot['timeRange']['initTimestamp'],
                "end_timestamp": snapshot['timeRange']['endTimestamp'],
                "replaced_snapshots_hashes": ','.join(snapshot['replacedSnapshotHashes']),
                "number_of_entities": snapshot['numberOfEntities'],
                "generation_timestamp": snapshot['generationTimestamp'],
            }

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        self.logger.info(f'get context child {record["hash"]}')

        return {
            "hash": record['hash']
        }

    schema = PropertiesList(
        Property("hash", StringType, required=True),
        Property("init_timestamp", IntegerType),
        Property("end_timestamp", IntegerType),
        Property("replaced_snapshots_hashes", StringType),
        Property("number_of_entities", IntegerType),
        Property("generation_timestamp", IntegerType),
    ).to_dict()


class SceneMappingStream(DecentralandStreamAPIStream):
    name = "scene_mapping"
    path = "/content/contents/{hash}"
    primary_keys = ['global_hash', 'scene_hash']
    parent_stream_type = ContentSnapshotStream

    def parse_response(self, response) -> Iterable[dict]:
        """Parse data"""

        for line in response.iter_lines():
            # Avoid header line
            if line is None or line == b'### Decentraland json snapshot':
                continue

            data = json.loads(line)

            # Avoid mapping other entities
            if data['entityType'] != 'scene':
                continue

            yield {
                "scene_hash": data['entityId'],
                "parcels": data['pointers']
            }

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "scene_hash": record['scene_hash']
        }

    def post_process(self, row: dict, context: Optional[dict]) -> dict:
        """Post process a row"""
        row['global_hash'] = context['hash']

        return row

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

    def request_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Need to override to avoid reprocessing data"""

        state = self.get_context_state(context)

        if 'scene_hashes' in state:
            self.logger.warn(
                f"(stream: {self.name}) Skipping any hash matching {len(state['scene_hashes'])} saved hashes")
        else:
            self.logger.warn(
                f"(stream: {self.name}) No existing hashes saved, full sync")
            state['scene_hashes'] = []

        if context['scene_hash'] in state['scene_hashes']:
            self.logger.warn(
                f"(stream: {self.name}) Skipping requesting hash {context['scene_hash']}")
            return []

        prepared_request = self.prepare_request(
            {"id": context['scene_hash']}, context, next_page_token=None
        )

        response = self._request_with_backoff(prepared_request, context)

        parsedResponse = self.parse_response(response)

        for row in parsedResponse:
            yield row

        state['scene_hashes'].append(context['scene_hash'])

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException),
        max_tries=8,
        giveup=lambda e: e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429,
        factor=2,
    )
    def _request_with_backoff(
        self, prepared_request, context: Optional[dict]
    ) -> requests.Response:
        response = self.requests_session.send(prepared_request)
        if self._LOG_REQUEST_METRICS:
            extra_tags = {}
            if self._LOG_REQUEST_METRIC_URLS:
                extra_tags["url"] = cast(str, prepared_request.path_url)
            self._write_request_duration_log(
                endpoint=self.path,
                response=response,
                context=context,
                extra_tags=extra_tags,
            )
        if response.status_code in [401, 403]:
            self.logger.info(
                "Failed request for {}".format(prepared_request.url))
            self.logger.info(
                f"Reason: {response.status_code} - {str(response.content)}"
            )
            raise RuntimeError(
                "Requested resource was unauthorized, forbidden, or not found."
            )
        if response.status_code == 429:
            self.logger.info(
                "Throttled request for {}".format(prepared_request.url))
            raise requests.exceptions.RequestException(
                request=prepared_request,
                response=response
            )
        elif response.status_code >= 400:
            raise RuntimeError(
                f"Error making request to API: {prepared_request.url} "
                f"[{response.status_code} - {str(response.content)}]".replace(
                    "\\n", "\n"
                )
            )

        return response

    def prepare_request(
        self, params: dict, context: Optional[dict], next_page_token: Optional[Any]
    ) -> requests.PreparedRequest:
        """Prepare a request object.

        If partitioning is supported, the `context` object will contain the partition
        definitions. Pagination information can be parsed from `next_page_token` if
        `next_page_token` is not None.
        """
        http_method = self.rest_method
        url: str = self.get_url(context)
        request_data = self.prepare_request_payload(context, next_page_token)
        headers = self.http_headers

        request = cast(
            requests.PreparedRequest,
            self.requests_session.prepare_request(
                requests.Request(
                    method=http_method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=request_data,
                )
            ),
        )
        return request

    def parse_response(self, response) -> Iterable[dict]:
        """Parse data"""

        data = response.json()
        for row in data:
            yield row

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Rename and flatten some fields"""
        row['scene_hash'] = row['id']
        del row['id']

        row['content_files'] = len(row['content'])

        # Flatten some properties into json strings
        metadata = row.get('metadata')
        if metadata:
            row['metadata'] = processSceneMetadata(metadata)
        return row

    schema = PropertiesList(
        Property("scene_hash", StringType, required=True),
        Property("type", StringType),
        Property("timestamp", IntegerType),
        Property("content_files", IntegerType),
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
            Property("source", StringType),
            Property("requiredPermissions", StringType),
            Property("spawnPoints", StringType),
            Property("tags", StringType),

        )),

    ).to_dict()


class SceneChangesStream(DecentralandStreamAPIStream):
    name = "scene_changes"
    path = "/content/pointer-changes"
    primary_keys = ['scene_hash']
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
            "entityType": "scene",
            "lastId": self.last_id
        }

    def get_replication_key_signpost(
        self, context: Optional[dict]
    ) -> Optional[Union[datetime, Any]]:
        one_day_ago = utc_now() - timedelta(hours=24)
        return int(one_day_ago.timestamp() * 1000)

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Rename and flatten some fields"""
        row['scene_hash'] = row['entityId']
        self.last_id = row['scene_hash']
        del row['entityId']

        row['entityTimestamp'] = int(row['entityTimestamp'])
        row['localTimestamp'] = int(row['localTimestamp'])

        metadata = row.get('metadata')
        if metadata:
            row['metadata'] = processSceneMetadata(metadata)

        return row

    schema = PropertiesList(
        Property("scene_hash", StringType, required=True),
        Property("type", StringType),
        Property("localTimestamp", IntegerType),
        Property("entityTimestamp", IntegerType),
        Property("type", StringType),
        Property("version", StringType),
        Property("metadata", ObjectType(
            Property("display", ObjectType(
                Property("title", StringType),
                Property("description", StringType),
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
            Property("source", StringType),
            Property("requiredPermissions", StringType),
            Property("spawnPoints", StringType),
            Property("tags", StringType),

        )),

    ).to_dict()


class SceneChangesStreamV2(DecentralandStreamAPIStream):
    name = "scene_changes_v2"
    path = "/content/pointer-changes"
    primary_keys = ['scene_hash']
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
            "entityType": "scene",
            "lastId": self.last_id
        }

    def get_replication_key_signpost(
        self, context: Optional[dict]
    ) -> Optional[Union[datetime, Any]]:
        one_day_ago = utc_now() - timedelta(hours=24)
        return int(one_day_ago.timestamp() * 1000)

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Rename and flatten some fields"""
        row['scene_hash'] = row['entityId']
        self.last_id = row['scene_hash']
        del row['entityId']

        row['entity_timestamp'] = int(row['entityTimestamp'])
        row['local_timestamp'] = int(row['localTimestamp'])

        row['metadata'] = json.dumps(row.get('metadata', {}))

        return row

    schema = PropertiesList(
        Property("scene_hash", StringType, required=True),
        Property("type", StringType),
        Property("local_timestamp", IntegerType),
        Property("entity_timestamp", IntegerType),
        Property("type", StringType),
        Property("version", StringType),
        Property("metadata", StringType),
    ).to_dict()
