import os
import logging
import json

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
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
    start_date = args.config.get("start_date")

    state = args.state

    credentials = get_authorized_http(credentials_file)
    service = build("webmasters", "v3", credentials=credentials)

    stream.process_streams(
        service,
        site_urls,
        dimensions,
        state=state,
        stream_id=stream_id,
        start_date=start_date,
    )


def get_authorized_http(credentials_file):
    with open(credentials_file, "r") as fp:
        json_file = fp.read()

    return OAuth2Credentials.from_json(json_file)


if __name__ == "__main__":
    main()
