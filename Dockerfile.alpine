FROM python:3-alpine

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apk add --no-cache \
            --upgrade \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
        postgresql-client gcc \
        && apk add --no-cache \
            --upgrade \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/community \
        geos 
RUN apk add --no-cache \
            --upgrade \
            --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
            --virtual .build-deps \
        postgresql-dev python3-dev musl-dev libc-dev 

RUN apk add --virtual .build-deps \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/main \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/community \
        gcc libc-dev geos-dev geos && \
    runDeps="$(scanelf --needed --nobanner --recursive /usr/local \
    | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
    | xargs -r apk info --installed \
    | sort -u)" && \
    apk add --virtual .rundeps $runDeps

RUN geos-config --cflags

COPY requirements.txt /app

RUN python3 -m pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt  --no-cache-dir 

RUN apk --purge del .build-deps 

COPY . /app

VOLUME ["/config"]

EXPOSE 8080

COPY docker-entrypoint.sh /usr/bin/docker-entrypoint.sh


ENTRYPOINT [ "docker-entrypoint.sh" ]
