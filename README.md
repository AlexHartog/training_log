# Training Log

[![Django CI](https://github.com/AlexHartog/training_log/actions/workflows/django.yml/badge.svg)](https://github.com/AlexHartog/training_log/actions/workflows/django.yml)
[![Docker Compose Build](https://github.com/AlexHartog/training_log/actions/workflows/docker.yml/badge.svg)](https://github.com/AlexHartog/training_log/actions/workflows/docker.yml)


## Installation


#### Database

A database needs to be set up. A user needs to be created for the django project and giving permissions to create 
tables and do crud operations. 

#### Configuration

Create a .env file in the root directory.

The STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET can be set up through the strava website. Profile -> Settings -> My 
API Application.

The SECRET_KEY needs to be configured with any value. Recommended would be to use django to generate this. This can 
be done with the following command.

`python .\training_log\manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

This needs the following config:

~~~
DB_ENGINE=
DB_SCHEMA=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
SECRET_KEY=
# OPTIONAL SETTINGS
COMPOSE_PROJECT_NAME=
DJANGO_PORT=
STRAVA_SYNC_COUNT=
NGINX_PORT=
DJANGO_DEBUG=
DJANGO_LOG_LEVEL=
HOST_OVERRIDE=
REDIS_HOST=
~~~


#### Docker Compose

The app can be started by running 

`docker-compose build` 

and subsequently

`docker-compose up -d`

Now the website can be accessed at *ip_address*:*nginx_port*



Afterwards logs can be read using 

`docker-compose logs` (add --follow for live logs)



#### Users

The super user can be created using 

`python .\training_log\manage.py createsuperuser`

Other users can be registered through the website. After registering a user, via 


#### Migrating in docker compose

Docker Compose should already contain the migrate command and apply migrations. However, if this fails, you can
enter the container to run migrations manually.

Run `docker ps` to get the container id of the training log container

Run `docker exec -t -i e0bfb46360dd python manage.py migrate`
(replace the container id with the one you got from the previous command)

Or to run directly in bash:
Run `docker exec -t -i 66175bfd6ae6 bash` 
(replace the container id with the one you got from the previous command)



## TODO
### First release
- [x] Add a good overview of all training
- [x] Create a cronjob for strava imports (implemented using huey)
- [x] Clean up data
- [x] Add a link to add manual training
- [x] Convert duration from minutes to seconds for new training

### Later releases
- [ ] More statistics 
- [ ] Calendar
- [ ] Supplement existing training data with strava data
- [x] Graphs
- [ ] Additional graphs
- [ ] Add HTTPS
- [x] Save JSON data from strava
- [x] Move to proper logger
- [x] Add activity zones
- [ ] CRUD operations
- [x] Squash migrations
- [x] Add strava import action on an activity
- [x] How to deal with too many requests to strava when getting activity zones?
- [x] Implement Strava webhooks
- [x] Add more athlete data
- [x] Save strava athlete id
- [x] Delete invalid subscription
- [x] Check if athlete has premium before checking zones

### Important 
- [x] Fix migrations in docker compose. What is happening? It thinks it's on version 1
- [x] Migrations still causing issues. How do we deal with migrations if database is not in line with database
- [x] Max port part of .env with a default
- [x] Make port for nginx configurable
- [x] Fix static files for development server


