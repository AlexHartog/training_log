FROM python:3.11

ENV APP_HOME=/home/app/web

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN groupadd -r app && useradd -r -g app app

# create the appropriate directories
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip --root-user-action=ignore
RUN pip install -r requirements.txt --root-user-action=ignore


# copy entrypoint.prod.sh
COPY entrypoint.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/entrypoint.sh
RUN chmod +x  $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

RUN chown -R app:app $APP_HOME

# change to the app user
USER app

ENTRYPOINT ["/bin/sh", "/home/app/web/entrypoint.sh"]
