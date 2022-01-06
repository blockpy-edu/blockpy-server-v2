FROM python:3.8

RUN apk add --update \
    build-base libffi-dev openssl-dev \
    xmlsec xmlsec-dev \
  && rm -rf /var/cache/apk/*

ADD requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

EXPOSE 9001
CMD python main.py