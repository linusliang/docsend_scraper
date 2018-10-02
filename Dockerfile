FROM python:3.6-alpine

MAINTAINER Michael Benoit "mbenoit2012@gmail.com"

RUN apk update
RUN apk add make g++ zlib-dev jpeg-dev

COPY . /opt/doc_scraper/
WORKDIR /opt/doc_scraper
EXPOSE 5000

RUN python setup.py install

ENV FLASK_ENV production
ENV FLASK_APP autoapp.py

ENTRYPOINT ["python", "autoapp.py"]
