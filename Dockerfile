FROM python:3.7-alpine3.10

RUN apk add --quiet --no-cache \
    gcc g++ make libffi-dev openssl-dev

COPY . /app

WORKDIR /app

RUN python setup.py install

RUN snmpagent-unity create-community --name public

ENTRYPOINT [ "snmpagent-unity" ]

CMD ["run", "--conf_file", "/app/unity.ini"]