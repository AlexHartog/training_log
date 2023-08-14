FROM python:3.11-slim

WORKDIR /training_log

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/

ENTRYPOINT ["entrypoint.sh"]
