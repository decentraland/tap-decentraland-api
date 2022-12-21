"""Stream class for tap-decentraland-api."""


import datetime, time
import requests


from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable


from tap_decentraland_api.client import BaseAPIStream


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

def escape_backslashes(variable):
    if isinstance(variable, str):
        return variable.replace('\\', '\\\\')

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class SnapshotDaoStream(BaseAPIStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["governance_snapshot_api_url"]


    def parse_response(self, response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()
        try:
            results = resp_json["data"]
            for row in results:                
                yield row
        except Exception as err:
            self.logger.warn(f"(stream: {self.name}) Problem with response: {resp_json}")
            raise err

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Any:
        """Return token identifying next page or None if all records have been read."""
        
        resp_json = response.json()
        results = resp_json["data"]
        results_len = len(results)

        old_token = previous_token or 0
        
        if results_len == self.RESULTS_PER_PAGE:
            next_page_token = old_token + self.RESULTS_PER_PAGE
            self.logger.info(f"Next page: {next_page_token}")
            return next_page_token
        else:
            self.logger.info(f"No more pages")
            return None # Finished if we have less than RESULTS_PER_PAGE


    def get_url_params(
        self,
        context: Optional[dict],
        next_page_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        offset = 0
        if next_page_token:
            offset = next_page_token
        return {"limit": self.RESULTS_PER_PAGE, "offset": offset}



class SnapshotDaoChildStream(BaseAPIStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["governance_snapshot_api_url"]



class SnapshotProposalsStream(SnapshotDaoStream):
    name = "dao_snapshot_proposals"

    path = "/proposals"

    primary_keys = ['rowId']
    replication_key = None
       

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['id'],row['updated_at']])

        # Escape backslashes   
        row['snapshot_proposal']['name'] = escape_backslashes(row['snapshot_proposal'].get('name'))
        row['snapshot_proposal']['body'] = escape_backslashes(row['snapshot_proposal'].get('body'))
        row['snapshot_proposal']['snapshot'] = int(row['snapshot_proposal'].get('snapshot'))
        row['title'] = escape_backslashes(row.get('title'))
        row['description'] = escape_backslashes(row.get('description'))
        row['enacted_description'] = escape_backslashes(row.get('enacted_description'))
        row['configuration']['description'] = escape_backslashes(row['configuration'].get('description'))
        row['configuration']['abstract'] = escape_backslashes(row['configuration'].get('abstract'))
        row['configuration']['specification'] = escape_backslashes(row['configuration'].get('specification'))
        row['configuration']['personnel'] = escape_backslashes(row['configuration'].get('personnel'))
        row['configuration']['roadmap'] = escape_backslashes(row['configuration'].get('roadmap'))

        # Convert to PSV
        row['snapshot_proposal']['choices'] = "|".join([escape_backslashes(x).replace('|', '_') for x in row['snapshot_proposal']['choices']])

        return row

    
    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """Return a context dictionary for child streams."""
        return {
            "proposalId": record['id'],
            "end": record['snapshot_proposal']['end']
        }

    schema = PropertiesList(
        Property("id", StringType, required=True),
        Property("rowId", StringType, required=True),
        Property("snapshot_id", StringType),
        Property("snapshot_space", StringType),
        Property("snapshot_proposal", ObjectType(
            Property("name", StringType),
            Property("body", StringType),
            Property("choices", StringType),
            Property("snapshot", IntegerType),
            Property("start", IntegerType),
            Property("end", IntegerType),
        )),
        Property("snapshot_signature", StringType),
        Property("snapshot_network", StringType),
        Property("discourse_id", IntegerType),
        Property("discourse_topic_id", IntegerType),
        Property("discourse_topic_slug", StringType),
        Property("user", StringType),
        Property("type", StringType),
        Property("status", StringType),
        Property("title", StringType),
        Property("description", StringType),
        Property("configuration", ObjectType(
            Property("description", StringType),
            # POI
            Property("x", IntegerType),
            Property("y", IntegerType),

            # Grants
            Property("abstract", StringType),
            Property("category", StringType),
            Property("tier", StringType),
            Property("size", IntegerType),
            Property("specification", StringType),
            Property("personnel", StringType),
            Property("roadmap", StringType),

            # Catalysts
            Property("owner", StringType),
            Property("domain", StringType),
        )),
        Property("enacted", BooleanType),
        Property("enacted_description", StringType),
        Property("deleted", BooleanType),
        Property("enacted_by", StringType),
        Property("deleted_by", StringType),
        Property("start_at", StringType),
        Property("finish_at", StringType),
        Property("created_at", StringType),
        Property("updated_at", StringType),
    ).to_dict()


class SnapshotVotesStream(SnapshotDaoChildStream):
    name = "dao_snapshot_votes"

    path = "/votes"

    primary_keys = ['rowId']
    replication_key = 'timestamp'
    ignore_parent_replication_keys = True
    
    parent_stream_type = SnapshotProposalsStream

    def get_records(self, context: Optional[dict]) -> Iterable[Dict[str, Any]]:
        """Return a generator of row-type dictionary objects.

        Each row emitted should be a dictionary of property names to their values.
        """

        endDate = datetime.datetime.fromtimestamp(context['end'])
        today = datetime.datetime.now()
        if endDate < today:
            try:
                lastDownload = self.get_starting_timestamp(context)
                if lastDownload is not None:
                    # Only download last 2 days after voting finishes
                    dtime = today - endDate
                    days = (dtime.total_seconds() / 3600 / 24)
                    if days > 2:
                        return
            except:
                self.logger.warn('Could not get starting timestamp')

        
        time.sleep(0.75)
        for row in self.request_records(context):
            row = self.post_process(row, context)
            yield row

    def get_url_params(self, context, next_page_token: Optional[IntegerType] = None) -> dict:
        return {
            "id": context['proposalId']
        }
    

    def parse_response(self, response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()
        try:
            results = resp_json["data"]
            for proposal, votes in results.items():
                for voter, vote in votes.items():
                    yield {
                            "proposal_id": proposal,
                            "voter": voter,
                            "choice": vote.get('choice'),
                            "voting_power": vote.get('vp'),
                            "timestamp": vote.get('timestamp')
                            }
        except Exception as err:
            self.logger.warn(f"(stream: {self.name}) Problem with response: {resp_json}")
            raise err
    
    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        """Generate row id"""
        row['rowId'] = "|".join([row['proposal_id'],row['voter']])
        row['timestamp'] = datetime.datetime.fromtimestamp(row['timestamp'])

        return row
    
    schema = PropertiesList(
        Property("proposal_id", StringType, required=True),
        Property("rowId", StringType, required=True),
        Property("voter", StringType, required=True),
        Property("choice", IntegerType),
        Property("voting_power", IntegerType),
        Property("timestamp", DateTimeType),
    ).to_dict()