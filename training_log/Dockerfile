FROM python:3.11-slim

# Install redis
RUN apt-get update
RUN apt-get --assume-yes install redis

WORKDIR /training_log

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
