"""Stream class for tap-decentraland-api."""


import requests, backoff, time


from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable, cast


from singer_sdk.streams import RESTStream



class BaseAPIStream(RESTStream):
    
    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException),
        max_tries=10,
        giveup=lambda e: e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429 and e.response.status_code != 502,
        factor=3,
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
            self.logger.info("Failed request for {}".format(prepared_request.url))
            self.logger.info(
                f"Reason: {response.status_code} - {str(response.content)}"
            )
            raise RuntimeError(
                "Requested resource was unauthorized, forbidden, or not found."
            )
        if response.status_code == 429:
            self.logger.info("Throttled request for {}".format(prepared_request.url))
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


