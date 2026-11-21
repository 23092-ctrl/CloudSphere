FROM python:3.12-alpine

WORKDIR /app

# Install postgres client library dependencies for alpine
RUN apk add --no-cache libpq postgresql-libs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "app:app"]
