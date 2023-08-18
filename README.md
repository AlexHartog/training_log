# Training Log

## Installation

#### Configuration

Create a .env file in the root directory.

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
# OPTIONAL SETTINGS
COMPOSE_PROJECT_NAME=
DJANGO_PORT=
~~~




#### Docker Compose





#### Migrating in docker compose

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
- [] Clean up data
- [x] Add a link to add manual training
- [x] Convert duration from minutes to seconds for new training

### Later releases
- [] More statistics 
- [] Calendar
- [] Supplement existing training data with strava data

### Important 
- [x] Fix migrations in docker compose. What is happening? It thinks it's on version 1
- [] Migrations still causing issues. How do we deal with migrations if database is not in line with database
- [x] Max port part of .env with a default


## Notes

### Django migrations
Django builds migrations based on difference between the models and the migration files. 
So if the database is ahead of migrations, you will get a weird state and migrations
won't work. Making migration files part of the upload, helps solve this problem.

The state of migrations is stored in the database in the table django_migrations. If
it thinks migrations aren't applied, but they are, you can fake run all migrations using
`python manage.py migrate --fake`.

### Huey
Need to set up a redis server. Can't connect to this using localhost, but need to use 
the docker container name. This is because the huey container is in the same network
as the redis container.

To add periodic tasks, you need to create a tasks.py file in an app folder which is 
imported in the settings.py.

