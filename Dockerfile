FROM python:3-alpine

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apk add --no-cache \
            --upgrade \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
        postgresql-client \
    && apk add --no-cache \
            --upgrade \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
            --virtual .build-deps \
        postgresql-dev gcc python3-dev musl-dev

COPY requirements.txt /app

RUN python3 -m pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt  --no-cache-dir \
    && apk --purge del .build-deps

COPY . /app

VOLUME ["/config"]

EXPOSE 8080

COPY docker-entrypoint.sh /usr/bin/docker-entrypoint.sh

ENTRYPOINT [ "docker-entrypoint.sh" ]