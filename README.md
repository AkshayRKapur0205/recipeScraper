# Recipe Scraper API

A small Flask API that passes a recipe-page URL to the `recipe-scrapers`
dependency and returns six recipe fields as JSON. The application is defined in
[app.py](app.py); its dependencies are listed in
[requirements.txt](requirements.txt).

## Local setup

Use a Python 3 installation with `venv` and `pip` that is supported by the declared
dependencies. This repository does not pin a Python version or dependency
versions.

```text
git clone https://github.com/AkshayRKapur0205/recipeScraper.git
cd recipeScraper
```

Create an isolated environment and install the declared dependencies. These
commands use the environment's interpreter directly, so activation is not needed.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

**macOS / Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Running `app.py` starts Flask's built-in development server on `0.0.0.0`, which
listens on all network interfaces. Use `http://127.0.0.1:5000` for local requests.
The `PORT` environment variable changes the port and must be an integer; it
defaults to `5000` when unset. This development command is distinct from the
Gunicorn deployment command below.

## Endpoints

### `GET /`

Returns status `200` with the following string body (Flask's default `text/html`
content type):

```text
Recipe Scraper API is running. Use /scrape?url=...
```

### `GET /scrape?url=RECIPE_PAGE_URL`

The `url` query parameter is required. URL-encode its value, especially when the
recipe-page URL contains its own query parameters. The decoded value is passed
to `scrape_me` without application-level URL validation or normalization.

For example, replace `RECIPE_PAGE_URL` with the page you want to parse before
running this local request:

```powershell
curl.exe --get --data-urlencode "url=RECIPE_PAGE_URL" "http://127.0.0.1:5000/scrape"
```

On macOS / Linux, use `curl` instead of `curl.exe`.

A successful response has status `200` and content type `application/json`.
The following is illustrative fixture data used by the mocked tests, not the
result of a verified live scrape. The `.example` image URL is a placeholder.

```json
{
  "title": "Lemon pasta",
  "total_time": 35,
  "yields": "2 servings",
  "ingredients": [
    "200 g spaghetti",
    "1 lemon",
    "2 tbsp olive oil"
  ],
  "instructions": "1. Cook the pasta.\n2. Toss with lemon and olive oil.",
  "image": "https://recipes.example/lemon-pasta.jpg"
}
```

The keys come directly from the scraper methods `title()`, `total_time()`,
`yields()`, `ingredients()`, `instructions()`, and `image()`. The application
does not normalize these values or provide defaults. Their content and available
metadata depend on the page and the installed parser.

**Errors**

Omitting `url` or sending an empty value (`/scrape?url=`) returns status `400` and
JSON:

```json
{"error": "URL parameter is required"}
```

An exception from `scrape_me` or any of the six field accessors returns status
`500` and JSON containing the exception's string representation. For example,
the tests simulate a parser exception with this response:

```json
{"error": "Unable to parse recipe"}
```

That message is illustrative, not a fixed upstream error message. A failed field
accessor causes the whole request to fail; the application does not return
partial recipe data.

Both routes accept `GET`, with Flask's automatic `HEAD` and `OPTIONS` handling.
A `HEAD /scrape` request still performs extraction but returns no response body.
Unsupported methods such as `POST` return Flask's standard `405` HTML response,
not the JSON error bodies above.

## Deployment configuration

[render.yaml](render.yaml) declares a Render Python web service named
`recipe-api`, using the free plan and automatic deployment. Its build command is
`pip install -r requirements.txt`, and its start command is:

```sh
gunicorn app:app --bind 0.0.0.0:$PORT
```

Gunicorn imports the Flask application as `app:app` instead of running
`app.py` as a script. This command expects the deployment environment to supply
`PORT`; the script's `5000` fallback does not apply to it. Gunicorn is for
compatible Unix-like environments, not a native-Windows launch path.

The checked-in configuration does not establish that a live deployment exists.
All request examples here refer to a local server.

## Regression tests

From the repository root, after installing the declared dependencies, run:

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**macOS / Linux**

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The tests use Python's standard-library `unittest` and `unittest.mock` with
Flask's in-process test client. They patch `app.scrape_me` and check the home
response, field-preserving extraction and URL forwarding, missing/empty input,
parser and metadata exceptions, and method handling. They do not make website
requests, start a listening server, or require another service. No additional
test framework is required.

## Current limitations

- Live requests depend on upstream network access, page availability, and
  support in the installed `recipe-scrapers` version. Arbitrary URLs are not
  guaranteed to yield a recipe.
- Page changes, unsupported formats, and unavailable metadata can produce
  parser errors. The app does not add retries, caching, or partial-field recovery.
- Only the six fields above are returned. The app does not add nutrition,
  ingredient normalization, or other metadata exposed by some parsers.
- Dependencies are unpinned, so a fresh install can change parser behavior or
  compatibility. Mocked regression tests cover the Flask contract, not live
  website support or deployment readiness.
