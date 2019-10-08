import os
import sys
import json
from datetime import timedelta, date, datetime

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
import singer
from signer import utils

logger = singer.get_logger()

DIMENSIONS = ["country", "page", "query", "device", "date"]

service = None


def main():
    args = utils.parse_args(["oauth2_credentials_file"])

    dimensions = args.config.get("dimensions")
    if not dimensions:
        dimensions = DIMENSIONS
    else:
        for dim in dimensions:
            if dim not in DIMENSIONS:
                raise ValueError(f"unknown dimension: '{dim}'")

    credentials_file = args.config.get("oauth2_credentials_file")
    if not credentials_file:
        pass

    http = get_authorized_http(credentials_file)

    global service
    service = build("webmasters", "v3", http=http)


def build_streams(dimensions):
    verified_sites = verified_site_urls()
    for site in verified_sites:
        days = filter_days_with_data(service, site)
        records = get_analytics(site, days, dimensions)
        for record in records:
            logger.info(record)


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
            resp = (
                service.searchanalytics()
                .query(siteUrl=site_url, body=request)
                .execute()
            )
            dims = len(dimensions)
            for item in resp["rows"]:
                values = item.pop("keys")
                for i in range(dims):
                    key, value = dimensions[i], values[i]
                    item[key] = value
                item["timestamp"] = start_date
                yield item

            if len(resp["rows"]) < row_limit:
                break

            request["startRow"] += row_limit


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


def verified_site_urls():
    # Retrieve list of properties in account
    site_list = service.sites().list().execute()

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
    resp = service.searchanalytics().query(siteUrl=site_url, body=request).execute()

    # dates are sorted in ascending order
    for item in resp["rows"]:
        # example: 'keys': ['2019-09-09']
        yield item["keys"][0]


if __name__ == "__main__":
    main()
