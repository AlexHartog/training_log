FROM python:3.11-slim

# Install cron and any other required packages
RUN apt-get update && apt-get install -y cron
RUN apt-get --assume-yes install redis

WORKDIR /training_log

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

