import os

import logging

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
import singer
from singer import utils

from tap_googlesearch import stream

logger = singer.get_logger()

DIMENSIONS = ["country", "page", "query", "device", "date"]


def main():
    args = utils.parse_args(["oauth2_credentials_file"])

    dimensions = args.config.get("dimensions")

    credentials_file = args.config.get("oauth2_credentials_file") or os.environ.get(
        "OAUTH2_CREDENTIALS_FILE"
    )
    if not credentials_file:
        raise ValueError(
            "missing required config 'oauth2_credentials_file' or environment 'OAUTH2_CREDENTIALS_FILE'"
        )

    site_urls = args.config.get("site_urls")

    state = args.state

    http = get_authorized_http(credentials_file)
    service = build("webmasters", "v3", cache_discovery=False, http=http)

    stream.process_streams(service, site_urls, dimensions, state)


def get_authorized_http(credentials_file):
    with open(credentials_file, "r") as fp:
        raw_credentials = fp.read()
        credentials = OAuth2Credentials.from_json(raw_credentials)

        http = httplib2.Http()

        logger.info("refreshing credentials...")
        credentials.refresh(http)
        logger.info("done.")

    # write the new rotated credentials
    with open(credentials_file, "w") as fp:
        payload = credentials.to_json()
        fp.write(payload)

    http = httplib2.Http()
    return credentials.authorize(http)


if __name__ == "__main__":
    main()
