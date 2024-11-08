from singer_sdk.streams import RESTStream
from typing import Iterable, Optional
from singer_sdk.typing import (
    PropertiesList,
    Property,
    StringType,
    ArrayType,
    ObjectType
)


class BadgesStream(RESTStream):
    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["badges_url"]


class BadgesMetadataStream(BadgesStream):
    name = "badges_metadata"
    path = "/badges"
    primary_keys = ["badge_id"]
    records_jsonpath = "$.data[*]"
    replication_key = None
    schema = PropertiesList(
        Property("badge_id", StringType),
        Property("badge_name", StringType),
        Property("badge_category", StringType),
        Property("badge_description", StringType),
        Property("tiers", ArrayType(ObjectType(
            Property("tier_id", StringType, required=False),
            Property("tier_name", StringType, required=False),
            Property("tier_description", StringType, required=False)
        ))),

    ).to_dict()

    def parse_response(self, response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        resp_json = response.json()

        for row in resp_json.get("data"):
            result = {
                "badge_id": row.get("id"),
                "badge_name": row.get("name"),
                "badge_category": row.get("category"),
                "badge_description": row.get("description"),
                "tiers": []
            }

            if row.get("tiers"):
                for tier in row.get("tiers"):
                    tier = {
                        "tier_id": tier.get("tierId"),
                        "tier_name": tier.get("tierName"),
                        "tier_description": tier.get("description")
                    }

                    result["tiers"].append(tier)

            yield result
