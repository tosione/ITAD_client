# itad_client.py
# IsThereAnyDeal (ITAD) API client using OAuth2
#
# Author: Tosione
# Date: 2026-01-03

import requests_oauthlib
import requests
import webbrowser
import json
import os
import datetime
from print_color import print as printc
import private_data


'''
References:

ITAD API:
https://docs.isthereanydeal.com/

OAuth2:
https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html
https://docs.secureauth.com/ciam/en/proof-key-of-code-exchange--pkce-.html
https://bytebytego.com/guides/oauth-2-explained-with -siple-terms/
https://docs.authlib.org/en/latest/client/oauth2.html

HTML:
https://www.w3schools.com/tags/ref_httpmethods.asp
https://requests.readthedocs.io/en/latest/

JSON:
https://www.json.org/json-en.html
'''


# Application data
API_KEY = private_data.API_KEY
CLIENT_ID = private_data.CLIENT_ID
CLIENT_SECRET = private_data.CLIENT_SECRET
REDIRECT_URI = 'https://localhost'
SCOPE = ['user_info', 'notes_read', 'notes_write', 'profiles',
         'wait_read', 'wait_write', 'coll_read', 'coll_write']
AUTH_URL = 'https://isthereanydeal.com/oauth/authorize/'
TOKEN_URL = 'https://isthereanydeal.com/oauth/token/'
BASE_URL = 'https://api.isthereanydeal.com/'
TOKEN_FILE = 'itad_tokens.json'


def get_tokens(OASes):
    if os.path.exists(TOKEN_FILE):
        load_tokens_from_file(OASes)
        refresh_tokens_at_ITAD(OASes)
        save_tokens_to_file(OASes)
    else:
        obtain_new_tokens_from_ITAD(OASes)
        save_tokens_to_file(OASes)
        print(f'Created new tokens to file ({TOKEN_FILE})')


def load_tokens_from_file(OASes):
    OASes.token = load_json(TOKEN_FILE)


def save_tokens_to_file(OAses):
    save_json(TOKEN_FILE, OAses.token)


def save_json(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, check_circular=True)
    except Exception as e:
        print('Error saving JSON file:', e)


def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print('Error loading JSON file:', e)
        return None


def obtain_new_tokens_from_ITAD(OASes):
    # Step 1: obtain authorization URL
    authorization_url, state = OASes.authorization_url(AUTH_URL)

    # Step 2: open URL in browser, ask user to authorize and copy the redirect URL
    print('Please go to this URL and authorize access:')
    print(authorization_url)
    webbrowser.open(authorization_url)

    # Step 3: Get the authorization verifier code from the callback url
    redirect_URL = input('\nPaste the full redirect URL here: ')

    # Step 4: Fetch the access token
    OASes.fetch_token(TOKEN_URL, authorization_response=redirect_URL)

    print(f'Tokens expires in {OASes.token['expires_in']/3600/24} days.')
    print(
        f'Tokens expires at {datetime.datetime.fromtimestamp(OASes.token['expires_at'])}.')


def refresh_tokens_at_ITAD(OASes):
    OASes.refresh_token(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET))


def is_OAuth_ok(OASes):
    # Check if OAuth is OK by making a test request
    return OASes.get(BASE_URL + 'user/info/v2').status_code == 200


def get_data(OASes, security,  endpoint, params, data):
    URL = BASE_URL + endpoint
    headers = {'Content-Type': 'application/json'}
    if security == 'key':
        params['key'] = API_KEY
    elif security == 'oa2':
        headers['Authorization'] = 'Bearer ' + OASes.token['access_token']
    response = requests.get(URL, headers=headers, params=params, data=data)
    return response.json()


def put_data(OASes, security,  endpoint, params, data):
    URL = BASE_URL + endpoint
    headers = {'Content-Type': 'application/json'}
    params = {}
    if security == 'key':
        params['key'] = API_KEY
    elif security == 'oa2':
        headers['Authorization'] = 'Bearer ' + OASes.token['access_token']
    requests.put(URL, headers=headers, params=params, json=data)


def delete_data(OASes, endpoint, data):
    ...


def post_data(OASes, endpoint, data):
    ...


def patch_data(OASes, endpoint, data):
    ...


if __name__ == '__main__':
    # Clear console on Windows
    if os.name == 'nt':
        os.system('cls')

    # Create an OAuth2 Session
    OASes = requests_oauthlib.OAuth2Session(client_id=CLIENT_ID,
                                            redirect_uri=REDIRECT_URI,
                                            scope=SCOPE,
                                            pkce='S256')

    # Get tokens
    get_tokens(OASes)

    # Test OAuth
    if is_OAuth_ok(OASes):
        printc('OAuth is working', color='green')
    else:
        printc('OAuth is not working', color='red')

    # Handle real data here

    data_out = get_data(OASes=OASes,
                        security='oa2',
                        endpoint='user/notes/v1',
                        params={},
                        data={})
    save_json('user_notes.json', data_out)
    printc('Saved user_notes.json', color='cyan')

    data_out = get_data(OASes=OASes,
                        security='key',
                        endpoint='games/info/v2',
                        params={'id': '018d937f-11e6-715a-a82c-205cfda90ddd'},
                        data={})
    save_json('game_info.json', data_out)
    printc('Saved game_info.json', color='cyan')

    put_data(OASes=OASes,
             security='oa2',
             endpoint='user/notes/v1',
             params={},
             data=[{'gid': '018d937f-11e6-715a-a82c-205cfda90ddd',
                    'note': 'This is a test note 4'}])

    # x = put_data_custom(OASes)
