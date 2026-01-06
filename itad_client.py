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


def get_oauth_access_token():
    # Create an OAuth2 Session
    OASes = requests_oauthlib.OAuth2Session(client_id=CLIENT_ID,
                                            redirect_uri=REDIRECT_URI,
                                            scope=SCOPE,
                                            pkce='S256')

    if os.path.exists(TOKEN_FILE):
        OASes.token = load_json(TOKEN_FILE)
        OASes.refresh_token(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET))
        save_json(TOKEN_FILE, OASes.token)
    else:
        obtain_new_tokens_from_ITAD(OASes)
        save_json(TOKEN_FILE, OASes.token)
        print(f'Created new tokens to file ({TOKEN_FILE})')
    if test_OASes(OASes):
        return OASes.token['access_token']
    else:
        return None


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


def test_OASes(OASes):
    ok = OASes.get(BASE_URL + 'user/info/v2').status_code == 200
    if ok:
        printc('OAuth is working', color='green')
    else:
        printc('OAuth is not working', color='red')
    return ok


def send_request(security, method, endpoint, params, data):
    '''
    Docstring for get_data

    :param security: tipe of security ('key' or 'oa2')
    :param method: HTTP method ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
    :param endpoint: API endpoint
    :param params: parameters for the HTTP request
    :param data: body data for the HTTP request
    '''
    # prepare URL and headers
    URL = BASE_URL + endpoint
    headers = {'Content-Type': 'application/json'}
    if security == 'key':
        params['key'] = API_KEY
    elif security == 'oa2':
        headers['Authorization'] = 'Bearer ' + access_token

    if (method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
        resp = requests.request(method=method,
                                url=URL,
                                headers=headers,
                                params=params,
                                json=data)
        if resp.content == b'':
            return resp.status_code, None
        else:
            return resp.status_code, resp.json()
    else:
        print('Invalid HTTP method')
        return 0, None


if __name__ == '__main__':
    # Clear console on Windows
    if os.name == 'nt':
        os.system('cls')

    access_token = get_oauth_access_token()

    # test diferent endpoints, methods and security types
    res1, data1 = send_request(method='GET',
                               security='oa2',
                               endpoint='collection/groups/v1',
                               params={},
                               data={})
    save_json('data1.json', data1)
    print(f'Result 1: {res1} - Saved data1.json')

    res2, data2 = send_request(method='GET',
                               security='key',
                               endpoint='games/info/v2',
                               params={
                                   'id': '018d937f-11e6-715a-a82c-205cfda90ddd'},
                               data={})
    save_json('data2.json', data2)
    print(f'Result 2: {res2} - Saved data2.json')

    res3, data3 = send_request(method='PUT',
                               security='oa2',
                               endpoint='user/notes/v1',
                               params={},
                               data=[{'gid': '018d937f-11e6-715a-a82c-205cfda90ddd',
                                      'note': 'This is a test note {now}'}])
    print(f'Result 3: {res3}')

    res4, data4 = send_request(method='DELETE',
                               security='oa2',
                               endpoint='user/notes/v1',
                               params={},
                               data=['018d937f-11e6-715a-a82c-205cfda90ddd'])
    print(f'Result 4: {res4}')

    res5, data5 = send_request(method='POST',
                               security='oa2',
                               endpoint='collection/groups/v1',
                               params={},
                               data={"title": "New Collection Category",
                                     "public": False})
    print(f'Result 5: {res5}')

    res6, data6 = send_request(method='PATCH',
                               security='oa2',
                               endpoint='collection/groups/v1',
                               params={},
                               data=[{'id': 15099, 'title': 'Renamed Collection Category'}])
    save_json('data6.json', data6)
    print(f'Result 6: {res6} - Saved data6.json')
