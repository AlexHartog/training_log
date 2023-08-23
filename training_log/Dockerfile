#FROM python:3.11-slim
FROM python:3.11-alpine
#FROM python:3.9.6-alpine

#ENV MICRO_SERVICE=/home/app/microservice

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app && adduser -S app -G app
#RUN addgroup -S $APP_USER && adduser -S $APP_USER -G $APP_USER

#RUN mkdir -p $MICRO_SERVICE
#RUN mkdir -p $MICRO_SERVICE/static

#WORKDIR $MICRO_SERVICE

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# chown all the files to the app user
#RUN chown -R app:app $APP_HOME

# Copy the entrypoint script into the container
#COPY entrypoint_p.sh /usr/local/bin/
#COPY ./entrypoint_p.sh $MICRO_SERVICE
#RUN chmod +x /usr/local/bin/entrypoint_p.sh

# copy entrypoint.prod.sh
COPY ./entrypoint_p.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint_p.sh
RUN chmod +x  $APP_HOME/entrypoint_p.sh

# copy project
COPY . $APP_HOME

RUN chown -R app:app $APP_HOME

# change to the app user
USER app

#CMD ["/bin/bash", "/home/app/microservice/entrypoint.sh"]

ENTRYPOINT ["/home/app/web/entrypoint_p.sh"]
#ENTRYPOINT ["/home/app/microservice/entrypoint_p.sh"]
