FROM python:3.11-alpine

WORKDIR /app

# Install requirements
RUN apk add --no-cache \
            transmission-cli \
            gcc \
            musl-dev \
            libffi-dev \
            openssl-dev

# Copy files to container
COPY . /app

# Set default Google application credentials path
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/serviceAccountKey.json

# Install and build Addarr requirements
RUN pip install --no-cache-dir -r requirements.txt --upgrade

ENTRYPOINT ["python", "/app/src/addarr.py"]

