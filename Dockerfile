FROM python:slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y locales && \
    locale-gen fr_FR.UTF-8 


RUN apt-get update && \
        apt-get install -y postgresql-client gcc libgeos-dev 

COPY requirements.txt /app

RUN python3 -m pip install --upgrade pip --no-cache-dir \
    && pip install -r requirements.txt  --no-cache-dir 

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


COPY . /app

VOLUME ["/config"]

EXPOSE 8080

COPY docker-entrypoint.sh /usr/bin/docker-entrypoint.sh


ENTRYPOINT [ "docker-entrypoint.sh" ]
