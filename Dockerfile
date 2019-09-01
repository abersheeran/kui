FROM python:3.7-alpine

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
# Python, don't write bytecode!
ENV PYTHONDONTWRITEBYTECODE 1

# Install index.py in system
RUN apk add --no-cache --virtual .build-deps gcc libc-dev make \
    && pip3 install index.py \
    && apk del .build-deps gcc libc-dev make
