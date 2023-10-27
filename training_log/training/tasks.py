from huey.contrib.djhuey import task
from training.maps import TrainingMap


@task()
def load_map(selected_users, disciplines, start_date, end_date):
    training_map = TrainingMap()
    return training_map.create_training_map(
        selected_users, disciplines, start_date, end_date
    )
