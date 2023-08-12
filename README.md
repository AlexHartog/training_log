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
- [] Create a cronjob for strava imports (need to develop on Linux)
- [] Clean up data
- [x] Add a link to add manual training

### Later releases
- [] Statistics 
- [] Calendar
- [] Supplement existing training data with strava data

### Important 
- [] Fix migrations in docker compose. What is happening? It thinks it's on version 1


