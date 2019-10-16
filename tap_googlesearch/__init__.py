import os
import logging
import json

import httplib2
from apiclient.discovery import build
from oauth2client.client import AccessTokenCredentials 
import singer
from singer import utils

from tap_googlesearch import stream

logger = singer.get_logger()
logger.setLevel(logging.WARNING)

DIMENSIONS = ["country", "page", "query", "device", "date"]


def main():
    args = utils.parse_args([])

    dimensions = args.config.get("dimensions")

    credentials_file = args.config.get("oauth2_credentials_file") or os.environ.get(
        "OAUTH2_CREDENTIALS_FILE"
    )
    if not credentials_file:
        raise ValueError(
            "missing required config 'oauth2_credentials_file' or environment 'OAUTH2_CREDENTIALS_FILE'"
        )

    site_urls = args.config.get("site_urls")
    stream_id = args.config.get("stream_id")

    state = args.state

    http = get_authorized_http(credentials_file)
    service = build("webmasters", "v3", cache_discovery=False, http=http)

    stream.process_streams(service, site_urls, dimensions, state=state, stream_id=stream_id)


def get_authorized_http(credentials_file):
    with open(credentials_file, "r") as fp:
        json_creds = json.load(fp)

    credentials = AccessTokenCredentials(json_creds["access_token"], "tap-googlesearch-0.0.1")

    http = httplib2.Http()
    return credentials.authorize(http)


if __name__ == "__main__":
    main()
