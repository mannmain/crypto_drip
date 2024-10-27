FROM python:3.8-slim-buster

RUN mkdir /project

WORKDIR /project

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh
