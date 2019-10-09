#!/usr/bin/env python
import os
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
import httplib2


OAUTH2_CREDENTIALS_FILE = os.environ["OAUTH2_CREDENTIALS_FILE"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

try:
    with open(OAUTH2_CREDENTIALS_FILE, "r") as fp:
        raw_credentials = fp.read()
        credentials = OAuth2Credentials.from_json(raw_credentials)

        http = httplib2.Http()
        credentials.refresh(http)

except IOError:
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

with open(OAUTH2_CREDENTIALS_FILE, "w") as fp:
    payload = credentials.to_json()
    fp.write(payload)
