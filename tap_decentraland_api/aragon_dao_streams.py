"""Stream class for tap-decentraland-api."""


import requests


from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from singer_sdk.streams import GraphQLStream


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


from tap_decentraland_api.decode_evm_script import decodeScript

class AragonDaoStream(GraphQLStream):

    RESULTS_PER_PAGE = 100

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["governance_aragon_api_url"]


    def parse_response(self, response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()
        try:
            results = resp_json["data"][self.object_returned]
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
        results = resp_json["data"][self.object_returned]
        results_len = len(results)

        old_token = previous_token or 0
        self.logger.info(f"Old token: {old_token}")
        self.logger.info(f"Results: {results_len}")
        
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
        self.logger.info(f"Offset: {offset}")
        return {"limit": self.RESULTS_PER_PAGE, "offset": offset}


class AragonProposalsStream(AragonDaoStream):
    name = "dao_aragon_proposals"

    primary_keys = ['id']
    replication_key = None
    object_returned = 'votes'

    query = """
    query ($limit: Int!, $offset: Int!)
        {

        votes (
            first: $limit,
            skip: $offset,
            orderBy: startDate,
            orderDirection: asc,
            where:{
                orgAddress:"0xF47917B108ca4B820CCEA2587546fbB9f7564b56"
            })
            {
                id
                appAddress
                creator
                metadata
                executed
                startDate
                snapshotBlock
                supportRequiredPct
                script
                minAcceptQuorum
                yea
                nay
                votingPower
                voteNum
                castVotes {
                    id
                    voter{ address }
                    supports
                    stake
                    createdAt   
                }
            }
    }

    """

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        row['script_description'] = decodeScript(row['script'])
        return row

    

    schema = PropertiesList(
        Property("id", StringType),
        Property("appAddress", StringType),
        Property("creator", StringType),
        Property("metadata", StringType),
        Property("executed", BooleanType),
        Property("startDate", StringType),
        Property("snapshotBlock", StringType),
        Property("supportRequiredPct", StringType),
        Property("script", StringType),
        Property("script_description", StringType),
        Property("minAcceptQuorum", StringType),
        Property("yea", StringType),
        Property("nay", StringType),
        Property("votingPower", StringType),
        Property("voteNum", StringType),
        Property("castVotes", ArrayType(ObjectType(
            Property("id", StringType),
            Property("voter", ObjectType(
                Property("address", StringType),
            )),
            Property("supports", BooleanType),
            Property("stake", StringType),
            Property("createdAt", StringType),   
        )))
    ).to_dict()

