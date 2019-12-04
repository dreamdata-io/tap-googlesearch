# tap-googlesearch

### installation

Install using `pip`:

```bash
pip install tap-googlesearch
```

### example

```bash
tap-googlesearch -c config.json > records.ndjson
```

and test using the `singer-check-tap` by installing the `singer-tools` as well:

```bash
pipenv install tap-googlesearch singer-tools
pipenv run tap-googlesearch -c example_config.json | pipenv run singer-check-tap
```

### config

Below is an example of a valid `config.json` for this tap. There's an optional `start_date` field that will default to 24 weeks in the past if not set.

```json
{
  "oauth2_credentials_file": "<fully qualified path to the OAuth2.0 credentials file>",
  "dimensions": ["page", "query"],
  "start_date": "2018-05-23",
  "site_urls": ["<optional list of site_urls to include (defaults to all)>"]
}
```
