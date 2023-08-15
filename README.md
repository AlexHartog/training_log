# Training Log

## Installation

#### Virtual environment
Run `python -m venv venv` in the root of the project to create a virtual environment.

Activate the virtual environment using `source venv/bin/activate` (Linux) or 
`venv\Scripts\activate` (Windows).

#### Requirements
Install the requirements using `pip install -r requirements.txt`


#### Migrating in docker compose

Run `docker ps` to get the container id of the traininglog container
Run `docker exec -t -i 66175bfd6ae6 bash` (relace the container id with the one you got from the previous command)



## TODO
### First release
- [x] Add a good overview of all training
- [] Create a cronjob for strava imports (need to develop on Linux or use another scheduler)
- [] Clean up data
- [x] Add a link to add manual training

### Later releases
- [] Statistics 
- [] Calendar
- [] Supplement existing training data with strava data

### Important 
- [x] Fix migrations in docker compose. What is happening? It thinks it's on version 1
- [x] Max port part of .env with a default


## Notes

### Django migrations
Django builds migrations based on difference between the models and the migration files. 
So if the database is ahead of migrations, you will get a weird state and migrations
won't work. Making migration files part of the upload, helps solve this problem.

### Huey
Need to set up a redis server. Can't connect to this using localhost, but need to use 
the docker container name. This is because the huey container is in the same network
as the redis container.

To add periodic tasks, you need to create a tasks.py file in an app folder which is 
imported in the settings.py.

