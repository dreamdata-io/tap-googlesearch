import os
import logging
import json

from apiclient import discovery
from google.oauth2.credentials import Credentials

import singer
from singer import utils

from tap_googlesearch import stream

discovery.logger.setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)
logger = singer.get_logger()
logger.setLevel(logging.INFO)


DIMENSIONS = ["country", "page", "query", "device", "date"]


def main():
    args = utils.parse_args([])

    dimensions = args.config.get("dimensions")

    credentials_file = args.config.get("oauth2_credentials_file") or os.environ.get(
        "OAUTH2_CREDENTIALS_FILE"
    )

    access_token = args.config.get("access_token")
    refresh_token = args.config.get("refresh_token")
    client_id = args.config.get("client_id")
    client_secret = args.config.get("client_secret")

    credentials = get_credentials(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        credentials_file=credentials_file,
    )

    service = discovery.build(
        "webmasters", "v3", cache_discovery=False, credentials=credentials
    )

    site_urls = args.config.get("site_urls")
    stream_id = args.config.get("stream_id")
    start_date = args.config.get("start_date")

    state = args.state

    stream.process_streams(
        service,
        site_urls,
        dimensions,
        state=state,
        stream_id=stream_id,
        start_date=start_date,
    )


def get_credentials(
    client_id=None,
    client_secret=None,
    access_token=None,
    refresh_token=None,
    credentials_file=None,
):
    if (not refresh_token and not access_token) and credentials_file:
        with open(credentials_file, "r") as fp:
            json_file = json.load(fp)

        client_id = json_file.get("client_id")
        client_secret = json_file.get("client_secret")
        access_token = json_file.get("access_token")
        refresh_token = json_file.get("refresh_token")

    if not refresh_token and not access_token:
        raise ValueError(
            f"required field 'access_token' cannot be empty without a non-empty 'refresh_token' ({credentials_file} file)"
        )

    if not refresh_token:
        logger.warn(
            f"no 'refresh_token' in file {credentials_file} - unable to refresh when token expires"
        )

    return Credentials(
        access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )


if __name__ == "__main__":
    main()
