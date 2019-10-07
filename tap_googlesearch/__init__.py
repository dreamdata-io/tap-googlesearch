import os
import sys
import json
from datetime import timedelta, date

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]


def main():
    http = get_authorized_http()
    webmasters_service = build("webmasters", "v3", http=http)


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


if __name__ == "__main__":
    main()
