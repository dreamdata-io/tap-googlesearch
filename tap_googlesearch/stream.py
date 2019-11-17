import os
import pkg_resources
import json
import sys
import traceback

from typing import Dict, Any, List
from datetime import date, timedelta, datetime

import ratelimit
import backoff
import googleapiclient


import singer
from singer import utils


DIMENSIONS = ["country", "page", "query", "device", "date"]

logger = singer.get_logger()
svc = None


def process_streams(
    service, site_urls, dimensions, state=None, stream_id=None, start_date=None
):
    global svc
    svc = service

    bookmark_property = "timestamp"
    key_properties = dimensions

    if not dimensions:
        logger.info(f"no dimensions specified in config, defaulting to {dimensions}")
        dimensions = DIMENSIONS
    else:
        for dim in dimensions:
            if dim not in DIMENSIONS:
                raise ValueError(f"unknown dimension: '{dim}'")

    if not stream_id:
        stream_id = stream_id = "_".join(dimensions)

    verified_urls = verified_site_urls()
    if not site_urls:
        site_urls = verified_urls
    else:
        for site_url in site_urls:
            if site_url not in verified_urls:
                raise ValueError(
                    f"site_url '{site_url}' not in the list of verified site_urls: {verified_urls}"
                )

    # load schema from disk
    schema = load_schema()

    # write schema
    singer.write_schema(stream_id, schema, key_properties)

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    checkpoint_string = singer.get_bookmark(state, stream_id, bookmark_property)
    checkpoint = None
    checkpoint_backup = None
    if checkpoint_string:
        logger.info(f"[{stream_id}] previous state: {checkpoint_string}")
        checkpoint_backup = checkpoint = datetime.strptime(
            checkpoint_string, "%Y-%m-%d"
        )

    new_checkpoint = None
    with singer.metrics.record_counter(stream_id) as counter:
        try:
            for record, new_checkpoint in build_records(
                dimensions, site_urls, checkpoint=checkpoint, start_date=start_date
            ):
                singer.write_record(stream_id, record, time_extracted=utils.now())
                counter.increment(1)
        except Exception as err:
            logger.error(traceback.format_exc())
            logger.error(f"stream encountered an error: {str(err)}")
            raise

    logger.info(f"emitting last successfull checkpoint")

    checkpoint = new_checkpoint or checkpoint_backup
    if checkpoint:
        singer.write_bookmark(
            state, stream_id, bookmark_property, checkpoint.strftime("%Y-%m-%d")
        )

    logger.info(f"[{stream_id}] emitting state: {state}")

    singer.write_state(state)

    logger.info(f"[{stream_id}] done")


def build_records(dimensions, site_urls, start_date=None, checkpoint=None):
    if checkpoint:
        # make sure to start a day after the last checkpointed date
        # to ensure that we are not producing duplicate data
        start_date = (checkpoint + timedelta(days=1)).date()
    elif start_date:
        start_date = start_date.date()
    else:
        start_date = date.today() - timedelta(weeks=4 * 6)

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
    request = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": date.today().strftime("%Y-%m-%d"),
        "dimensions": ["date"],
    }

    resp = search_analytics(site_url, request)

    # dates are sorted in ascending order
    for item in resp.get("rows", []):
        # example: 'keys': ['2019-09-09']
        date_string = item["keys"][0]
        yield datetime.strptime(date_string, "%Y-%m-%d")


def get_analytics(site_url, days, dimensions, row_limit=None):
    row_limit = row_limit or 1000
    for start_date in days:
        end_date = start_date + timedelta(days=1)

        request = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": dimensions,
            "rowLimit": 1000,
            "startRow": 0,
        }

        dims = len(dimensions)
        while True:
            resp = search_analytics(site_url, request)
            rows = resp.get("rows", [])

            for item in rows:
                values = item.pop("keys")
                for i in range(dims):
                    key, value = dimensions[i], values[i]
                    if key == "date":
                        date = datetime.strptime(value, "%Y-%m-%d")
                        value = date.isoformat()
                    item[key] = value
                item["timestamp"] = start_date.isoformat()
                item["site_url"] = site_url
                yield item, start_date

            if len(rows) < row_limit:
                break

            request["startRow"] += row_limit


@backoff.on_exception(backoff.expo, googleapiclient.errors.HttpError)
@ratelimit.limits(calls=20 * 60, period=60, raise_on_limit=False)
def search_analytics(site_url, body):
    return svc.searchanalytics().query(siteUrl=site_url, body=body).execute()


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
