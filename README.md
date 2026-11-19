# Personal-Website

Source for [jayrothenberger.com](https://www.jayrothenberger.com), a small Django site
deployed on Heroku.

## Layout

- `mysite/`: project settings and root URLs.
- `personal/templates/personal/`: the pages. `base.html` holds the shared layout.
- `personal/static/orrery/`: the live voxel solar system drawn behind every page (wasm +
  WebGL2). Built artifacts only; the source is `~/abattler/orrery` (see its README to rebuild).
- `personal/static/`: images and the CV and resume PDFs. To update a PDF, replace the file
  here and keep the same name, so `/static/<name>.pdf` links keep working.
- `tools/favicon.py`: makes `favicon.ico` and `apple-touch-icon.png`, an MS Paint style
  portrait from `me.jpg`. Run `python3 tools/favicon.py` after changing the photo.

## Configuration

Settings come from environment variables:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | yes, unless `DEBUG=1` | none | Django signing key. |
| `DEBUG` | no | `0` | Set to `1` only for local development. |
| `ALLOWED_HOSTS` | no | the site's domains, plus localhost | Comma-separated host names. |
| `DATABASE_URL` | no | local `db.sqlite3` | Postgres URL, for example from Heroku Postgres. |
| `SECURE_HSTS_SECONDS` | no | `3600` | HSTS max-age. Raise it once HTTPS works on every domain. |

To generate a key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Local development

```bash
uv venv && uv pip install -r requirements.txt
DEBUG=1 .venv/bin/python manage.py runserver
```

To run the tests:

```bash
SECRET_KEY=test .venv/bin/python manage.py test
```

## Deploying to Heroku

1. Set the secret key once:
   `heroku config:set SECRET_KEY=<generated key> -a <app>`
2. Deploy. The Docker build and the Python buildpack both run `collectstatic`.
