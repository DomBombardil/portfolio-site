# Django Portfolio

A small Django portfolio site for showcasing projects, resume items, and
certificates with image galleries.

## Features
- Project listing and project detail pages with multiple images
- Resume and certificates sections backed by database models
- Admin interface for managing content
- Local media handling for uploaded images

## Tech Stack
- Python 3.12.6
- Django 5.2
- SQLite (default)
- django-bootstrap5
- gunicorn (for production)
- whitenoise (for production)


## Local Setup
1) Create and activate a virtual environment.
2) Install dependencies.
3) Run migrations and start the server.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create an admin user if you want to manage content via the admin UI:

```sh
python manage.py createsuperuser
```

## Routes
- `/` - landing page
- `/all_projects/` - list of all projects
- `/<id>/` - project detail page
- `/resume/` - resume items
- `/certificates/` - certificates
- `/admin/` - Django admin

## Media
Uploaded images are served from `MEDIA_ROOT` in development. See
`portfolio/settings.py` for `MEDIA_URL` and `MEDIA_ROOT`.

## Notes
- Database is not provided here so you need to run`python manage.py migrate`
 to create a fresh database.
