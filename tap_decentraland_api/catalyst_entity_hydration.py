"""Shared entity-metadata hydration for Catalyst change-feed streams.

/content/pointer-changes stopped embedding `metadata` on its delta records.
Streams built on that endpoint (scenes, stores, profiles) need to fetch it
from the entity itself instead. entityId is a content hash, so
/content/contents/{entityId} resolves any entity regardless of whether it's
still the active one at its pointer -- unlike /content/entities/active or
/content/entities/{type}, which only resolve the currently active entity and
return nothing for records later superseded at the same pointer, which is
the majority of records in these change feeds.
"""

from typing import Optional, cast

import backoff
import requests


class CatalystEntityHydrationMixin:
    """Mixin adding entity-metadata hydration to a RESTStream subclass.

    Expects the host class to provide `url_base`, `requests_session`,
    `logger`, and `name` (all standard RESTStream attributes).
    """

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
        if response.status_code >= 400:
            # Raise as a RequestException (not RuntimeError) for anything the
            # backoff decorator above should get a chance to retry -- 429 and
            # any 5xx. giveup= still gives up immediately on other 4xx.
            if response.status_code == 429:
                self.logger.info(
                    "Throttled request for {}".format(prepared_request.url))
            else:
                self.logger.info(
                    f"Error making request to API: {prepared_request.url} "
                    f"[{response.status_code} - {str(response.content)}]".replace(
                        "\\n", "\n"
                    )
                )
            raise requests.exceptions.RequestException(
                request=prepared_request,
                response=response
            )

        return response

    def _fetch_entity_metadata(self, entity_id: str) -> Optional[dict]:
        """Fetch an entity's metadata directly by content hash."""
        url = f"{self.url_base}/content/contents/{entity_id}"
        prepared_request = cast(
            requests.PreparedRequest,
            self.requests_session.prepare_request(
                requests.Request(method="GET", url=url)
            ),
        )

        try:
            response = self._request_with_backoff(prepared_request, None)
            metadata = response.json().get('metadata')
        except (requests.exceptions.RequestException, RuntimeError, ValueError) as e:
            self.logger.error(
                f"(stream: {self.name}) Failed to hydrate metadata for entity "
                f"{entity_id}: {e}"
            )
            return None

        if not metadata:
            self.logger.error(
                f"(stream: {self.name}) Entity {entity_id} returned no metadata "
                "even after hydration"
            )
        return metadata
