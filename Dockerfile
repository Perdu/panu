FROM alpine:3.13
MAINTAINER Célestin Matte <docker_panu@cmatte.me>

RUN apk add --update build-base python3 python3-dev mysql-client libxml2-dev libxslt-dev libffi-dev py3-mysqlclient py3-lxml && python3 -m ensurepip

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY docker/* /app/
COPY panu.py /app/
COPY panu.conf.docker /app/panu.conf

CMD ["python3", "panu.py"]
