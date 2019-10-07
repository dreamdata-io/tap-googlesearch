import os
import sys
import json
from datetime import timedelta, date, datetime

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]


def main():
    http = get_authorized_http()
    service = build("webmasters", "v3", http=http)

    dimensions = ["page", "query"]

    verified_sites = verified_site_urls(service)
    for site in verified_sites:
        days = filter_days_with_data(service, site)
        records = get_analytics(service, site, days, dimensions)


def get_analytics(service, site_url, days, dimensions, row_limit=None):
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

        resp = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        dims = len(dimensions)
        for item in resp["rows"]:
            values = item.pop("keys")
            for i in range(dims):
                key, value = dimensions[i], values[i]
                item[key] = value
            yield item


def get_authorized_http(filename="credentials.json"):
    try:
        with open(filename, "r") as fp:
            raw_credentials = fp.read()
            credentials = OAuth2Credentials.from_json(raw_credentials)

            http = httplib2.Http()
            credentials.refresh(http)
            return credentials.authorize(http)
    except IOError:
        pass

    # Check https://developers.google.com/webmaster-tools/search-console-api-original/v3/ for all available scopes
    OAUTH_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

    # Redirect URI for installed apps
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

    # Run through the OAuth flow and retrieve credentials
    flow = OAuth2WebServerFlow(
        GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI
    )
    authorize_url = flow.step1_get_authorize_url()
    print("Go to the following link in your browser: " + authorize_url)
    code = input("Enter verification code: ").strip()
    credentials = flow.step2_exchange(code)

    with open(filename, "w") as fp:
        payload = credentials.to_json()
        fp.write(payload)

    http = httplib2.Http()
    return credentials.authorize(http)


def verified_site_urls(service):
    # Retrieve list of properties in account
    site_list = service.sites().list().execute()

    # Filter for verified websites
    return [
        s["siteUrl"]
        for s in site_list["siteEntry"]
        if s["permissionLevel"] != "siteUnverifiedUser" and s["siteUrl"][:4] == "http"
    ]


def filter_days_with_data(service, site_url, start_date: date = None):
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
