import os
import pkg_resources
import json
import sys

from typing import Dict, Any, List
from datetime import date, timedelta, datetime

import singer
from singer import utils


DIMENSIONS = ["country", "page", "query", "device", "date"]

logger = singer.get_logger()
svc = None


def process_streams(service, site_urls, dimensions, state=None):
    global svc
    svc = service

    bookmark_property = "timestamp"
    key_properties = dimensions

    if not dimensions:
        logger.info(f"no dimensions specified in config, defaulting to {dimensions}")
        dimensions = DIMENSIONS
        stream_id = "_".join(DIMENSIONS)
    else:
        for dim in dimensions:
            if dim not in DIMENSIONS:
                raise ValueError(f"unknown dimension: '{dim}'")
        stream_id = "_".join(dimensions)

    verified_urls = verified_site_urls()
    if not site_urls:
        site_urls = verified_urls
    else:
        for site_url in site_urls:
            if site_url not in verified_urls:
                raise ValueError(
                    f"site_url '{site_url}' not in the list of verified site_urls: {verified_urls}"
                )

    checkpoint = singer.get_bookmark(state, stream_id, bookmark_property)
    if checkpoint:
        logger.info(f"[{stream_id}] previous state: {checkpoint}")

    # load schema from disk
    schema = load_schema()

    # write schema
    singer.write_schema(stream_id, schema, key_properties)

    checkpoint_backup = checkpoint
    new_checkpoint = None
    try:
        for record, new_checkpoint in build_records(
            dimensions, site_urls, checkpoint=checkpoint
        ):
            singer.write_record(stream_id, record, time_extracted=utils.now())
    except Exception as err:
        logger.error(f"stream encountered an error: {err}")
        logger.info(f"emitting last successfull checkpoint")

    checkpoint = new_checkpoint or checkpoint_backup

    singer.write_bookmark(state, stream_id, bookmark_property, checkpoint)

    logger.info(f"[{stream_id}] emitting state: {state}")

    singer.write_state(state)

    logger.info(f"[{stream_id}] done")


def build_records(dimensions, site_urls, checkpoint=None):
    if not checkpoint:
        start_date = date.today() - timedelta(weeks=4 * 6)
    else:
        start_date = datetime.strptime(checkpoint, "%Y-%m-%d").date()

    for site_url in site_urls:
        days = filter_days_with_data(site_url, start_date=start_date)
        yield from get_analytics(site_url, days, dimensions)


def verified_site_urls():
    # Retrieve list of properties in account
    site_list = svc.sites().list().execute()

    # Filter for verified websites
    return [
        s["siteUrl"]
        for s in site_list["siteEntry"]
        if s["permissionLevel"] != "siteUnverifiedUser" and s["siteUrl"][:4] == "http"
    ]


def filter_days_with_data(site_url, start_date: date = None):
    """retrieve all dates that have data in the interval end_date - start_date"""
    if not start_date:
        start_date = date.today() - timedelta(weeks=4 * 6)

    request = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": date.today().strftime("%Y-%m-%d"),
        "dimensions": ["date"],
    }
    resp = svc.searchanalytics().query(siteUrl=site_url, body=request).execute()

    # dates are sorted in ascending order
    for item in resp["rows"]:
        # example: 'keys': ['2019-09-09']
        yield item["keys"][0]


def get_analytics(site_url, days, dimensions, row_limit=None):
    row_limit = row_limit or 1000
    for start_date in days:
        end_date = (
            datetime.strptime(start_date, "%Y-%m-%d").date() + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": 1000,
            "startRow": 0,
        }

        while True:
            resp = svc.searchanalytics().query(siteUrl=site_url, body=request).execute()
            dims = len(dimensions)
            for item in resp["rows"]:
                values = item.pop("keys")
                for i in range(dims):
                    key, value = dimensions[i], values[i]
                    item[key] = value
                item["timestamp"] = start_date
                item["site_url"] = site_url
                yield item, end_date

            if len(resp["rows"]) < row_limit:
                break

            request["startRow"] += row_limit


def discover(dimensions):
    if not dimensions:
        stream_id = "_".join(DIMENSIONS)
    else:
        stream_id = "_".join(dimensions)

    streams = [
        {"tap_stream_id": stream_id, "stream": stream_id, "schema": load_schema()}
    ]
    return {"streams": streams}


def load_schema():
    filename = f"tap_googlesearch/schemas/record.json"
    filepath = os.path.join(
        pkg_resources.get_distribution("tap_googlesearch").location, filename
    )
    with open(filepath, "r") as fp:
        return json.load(fp)