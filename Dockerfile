FROM python:3.12.0-alpine3.17
LABEL maintainer="andrii.khamaza0gmail.com"

ENV PYTHOUNNBUFFERED 1

WORKDIR app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
