FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=0

WORKDIR /Personal-Website

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build-time only: collectstatic needs some key to import settings.
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

RUN adduser -D app
USER app

CMD ["gunicorn", "mysite.wsgi", "--log-file=-"]
