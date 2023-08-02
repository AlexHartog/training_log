import requests
import os
from dotenv import dotenv_values

from django.conf import settings

from .models import StravaAuth

config = dotenv_values(os.path.join(settings.BASE_DIR, '.env'))


def get_access_token():
    # Replace these values with your actual Strava API credentials
    client_id = config['STRAVA_CLIENT_ID']
    redirect_uri = 'http://127.0.0.1:8000/strava'

    # Step 1: Get the authorization URL
    authorization_url = f'https://www.strava.com/oauth/' \
                        f'authorize?client_id={client_id}&' \
                        f'redirect_uri={redirect_uri}&response_type=code' \
                        f'&scope=activity:read_all'

    return authorization_url

    # Step 2: Ask the user to authorize your application by visiting
    # the authorization URL.
    # The user will be redirected to the redirect URI with a code.

    # Step 3: Extract the code from the redirected URI and use it to
    # get the access token
    # code = 'CODE_FROM_REDIRECT_URI'
    # access_token_url = 'https://www.strava.com/oauth/token'
    # payload = {
    #     'client_id': client_id,
    #     'client_secret': client_secret,
    #     'code': code,
    #     'grant_type': 'authorization_code',
    # }
    #
    # response = requests.post(access_token_url, data=payload)
    # access_token = response.json()['access_token']


def save_auth(request):
    # Got new code, use it to save new StravaAuth object
    print("Received ", request.GET)
    print("Code is ", request.GET['code'])
    for scope in request.GET['scope'].split(','):
        print("Scope is ", scope)
    # print("Scope is ", request.GET['scope'])

    code = request.GET['code']
    scope = request.GET['scope'].split(
        ',') if 'scope' in request.GET else []

    access_token_url = 'https://www.strava.com/oauth/token'
    # TODO: Move to .env
    payload = {
        'client_id': config['STRAVA_CLIENT_ID'],
        'client_secret': config['STRAVA_CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
    }
    response = requests.post(access_token_url, data=payload)

    # TODO: Handle bad response
    if response.status_code == 200:
        print('POST request successful!')

        response_content = response.content.decode('utf-8')
        print('Response content:')
        print(response_content)
    else:
        print(
            f'POST request failed with status code {response.status_code}.')
        print(f'Errors: {response.content.decode("utf-8")}')

    access_token = response.json()['access_token']

    # Create a new StravaAuth object
    strava_auth = StravaAuth.objects.create(
        user=request.user,
        code=code,
        access_token=access_token,
        scope=scope
    )
    StravaAuth.objects.filter(user=request.user).delete()

    strava_auth.save()


def get_activities(access_token):
    activities_url = \
        'https://www.strava.com/api/v3/athlete/activities?per_page=1'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(activities_url, headers=headers)
    # TODO: Check for bad response
    return response.json()
