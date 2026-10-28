# Cashmere Termo landing page: Django behind gunicorn. Static files are collected into the image
# and served by WhiteNoise; the SQLite database and uploaded photos live in mounted volumes.

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_SYNC=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/srv/app/.venv/bin:$PATH" \
    MEDIA_ROOT=/data/media
WORKDIR /srv/app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . ./
RUN uv sync --frozen --no-dev
# Settings require SECRET_KEY; collectstatic doesn't use it, so a placeholder is enough here.
RUN SECRET_KEY=collectstatic python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "stocks_landingpage.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-"]
