# tap-googlesearch

# how to execute

run the following command in the root of the folder:

```bash
pipenv install . && pipenv run tap-googlesearch -c config.json > records.ndjson
```

# config

Below is an example of a valid `config.json` for this tap. There's an optional `start_date` field that will default to 24 weeks in the past if not set.

```json
{
  "oauth2_credentials_file": "<fully qualified path to the OAuth2.0 credentials file>",
  "dimensions": ["page", "query"],
  "start_date": "2018-05-23",
  "site_urls": ["<optional list of site_urls to include (defaults to all)>"]
}
```
