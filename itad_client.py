
"""
itad_client.py
IsThereAnyDeal (ITAD) API client using OAuth2 and API Key

Author: tosione
Date: 2026-01-03

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
    https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
JSON:
    https://www.json.org/json-en.html
"""

__version__ = '0.1'
__author__ = 'tosione'


# Standard library imports
import os
import webbrowser
import json
import datetime
import pandas

# Related third party imports
import requests_oauthlib
import requests
from print_color import print as printc
from varname import nameof


# Local application/library specific imports
import private_data


# Application data
API_KEY = private_data.API_KEY
CLIENT_ID = private_data.CLIENT_ID
CLIENT_SECRET = private_data.CLIENT_SECRET
REDIRECT_URI = 'https://localhost'
SCOPE = [
    'user_info',
    'notes_read',
    'notes_write',
    'profiles',
    'wait_read',
    'wait_write',
    'coll_read',
    'coll_write'
]
AUTH_URL = 'https://isthereanydeal.com/oauth/authorize/'
TOKEN_URL = 'https://isthereanydeal.com/oauth/token/'
BASE_URL = 'https://api.isthereanydeal.com/'
TOKEN_FILE = 'itad_tokens.json'


def get_access_token():
    # Create an OAuth2 Session
    oauth_session = requests_oauthlib.OAuth2Session(client_id=CLIENT_ID,
                                                    redirect_uri=REDIRECT_URI,
                                                    scope=SCOPE,
                                                    pkce='S256')

    if os.path.exists(TOKEN_FILE):
        oauth_session.token = load_json(TOKEN_FILE)
        oauth_session.refresh_token(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET))
        save_json(TOKEN_FILE, oauth_session.token)
    else:
        get_new_tokens_from_itad(oauth_session)
        save_json(TOKEN_FILE, oauth_session.token)
        print(f'Created new tokens to file ({TOKEN_FILE})')
    if test_oauth_session(oauth_session):
        return oauth_session.token['access_token']
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


def get_new_tokens_from_itad(oauth_session):
    """_summary_

    Args:
        oauth_session (_type_): _description_
    """
    # Step 1: obtain authorization URL
    authorization_url, state = oauth_session.authorization_url(AUTH_URL)

    # Step 2: open URL in browser, ask user to authorize and copy redirect URL
    print('Please go to this URL and authorize access:')
    print(authorization_url)
    webbrowser.open(authorization_url)

    # Step 3: Get the authorization verifier code from the callback url
    redirect_URL = input('\nPaste the full redirect URL here: ')

    # Step 4: Fetch the access token
    oauth_session.fetch_token(TOKEN_URL, authorization_response=redirect_URL)

    print('Tokens expires in ',
          oauth_session.token['expires_in']/3600/24, ' days')
    print('Tokens expires at ',
          datetime.datetime.fromtimestamp(oauth_session.token['expires_at']))


def test_oauth_session(oauth_session):
    ok = oauth_session.get(BASE_URL + 'user/info/v2').status_code == 200
    if ok:
        printc('OAuth is working', color='green')
    else:
        printc('OAuth is not working', color='red')
    return ok


def send_request(method, endpoint, security, params={}, header={}, body={}):
    """
    Docstring for get_data

    :param security: tipe of security ('key' or 'oa2')
    :param method: HTTP method ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
    :param endpoint: API endpoint
    :param params: parameters for the HTTP request
    :param headers: headers for the HTTP request
    :param data: body data for the HTTP request
    """

    header['Content-Type'] = 'application/json'

    if security == 'key':
        params['key'] = API_KEY
    elif security == 'oa2':
        header['Authorization'] = 'Bearer ' + access_token
    else:
        print('Invalid security type: valid ''key'' or ''oa2'' ')
        return 0, None

    if endpoint.startswith('http') or endpoint == "":
        print('Invalid endpoint')
        return 0, None
    else:
        url = BASE_URL + endpoint

    if (method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
        resp = requests.request(method=method,
                                url=url,
                                headers=header,
                                params=params,
                                json=body)
        if resp.status_code >= 400:
            # request error
            print(
                f'HTTP error code({resp.status_code}): {resp.reason}. {resp.json()['reason_phrase']}')
            if 'details' in resp.json():
                print(f'\tDetails: {resp.json()['details']}')
            return resp.status_code, None
        elif resp.content == b'':
            # request ok with empty response
            return resp.status_code, None
        else:
            # request ok
            return resp.status_code, resp.json()
    else:
        print('Invalid HTTP method')
        return 0, None


class ITADSearchGames:
    # https://docs.isthereanydeal.com/#tag/Lookup/operation/games-search-v1

    def __init__(self, game_title_to_search, max_results=None):
        self.game_title_to_search = game_title_to_search
        self.max_results = max_results
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'games/search/v1'
        security = 'key'
        params = {'title': self.game_title_to_search,
                  'results': self.max_results}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            df = pandas.DataFrame(self.response)

            self.found_games_id = df['id'].to_list()
            self.found_games_slug = df['slug'].to_list()
            self.found_games_title = df['title'].to_list()
            self.found_games_type = df['type'].to_list()
            self.found_games_mature = df['mature'].to_list()
            self.found_games_assets = df['assets'].to_list()

            self.found_games_number = len(self.found_games_id)


class ITADGetGameInfo:
    # https://docs.isthereanydeal.com/#tag/Game/operation/games-info-v2

    def __init__(self, game_id):
        self.game_id = game_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'games/info/v2'
        security = 'key'
        params = {'id': self.game_id}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        if self.response_code == 200:
            self.game_info = self.response
            # self.game_id = self.response['id']
            self.game_slug = self.response['slug']
            self.game_title = self.response['title']
            self.game_type = self.response['type']
            self.game_app_id = self.response['appid']
            self.game_urls = self.response['urls']


class ITADGetGamesFromWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'waitlist/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)

            self.waitlist_games_id = self.df['id'].to_list()
            self.waitlist_games_slug = self.df['slug'].to_list()
            self.waitlist_games_title = self.df['title'].to_list()
            self.waitlist_games_assets = self.df['assets'].to_list()
            self.waitlist_games_mature = self.df['mature'].to_list()
            self.waitlist_games_date_added = self.df['added'].to_list()


class ITADPutGamesIntoWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-put

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'PUT'
        endpoint = 'waitlist/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADDelGamesFromWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'DELETE'
        endpoint = 'waitlist/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADGetGamesFromCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'collection/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)

            self.collection_games_id = self.df['id'].to_list()
            self.collection_games_slug = self.df['slug'].to_list()
            self.collection_games_title = self.df['title'].to_list()
            self.collection_games_assets = self.df['assets'].to_list()
            self.collection_games_mature = self.df['mature'].to_list()
            self.collection_games_date_added = self.df['added'].to_list()


class ITADPutGamesIntoCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-put

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'PUT'
        endpoint = 'collection/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADDelGamesFromCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'DELETE'
        endpoint = 'collection/games/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADGetCopiesOfGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-get

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'collection/copies/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)
            self.games = pandas.DataFrame(self.df['game'].to_list())
            self.shops = pandas.DataFrame(self.df['shop'].to_list())

            self.copies_id = self.df['id'].to_list()
            self.copies_game_id = self.games['id'].to_list()
            self.copies_shop_id = self.shops['id'].to_list()
            self.copies_shop_name = self.shops['name'].to_list()
            self.copies_redeemed = self.df['redeemed'].to_list()
            self.copies_price = self.df['price'].to_list()
            self.copies_note = self.df['note'].to_list()
            self.copies_tags = self.df['tags'].to_list()
            self.copies_added = self.df['added'].to_list()


class ITADAddCopiesToGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-post

    def __init__(self, game_id, redeemed, shop_id=None, price=None, note=None, tags=None):
        self.game_id = game_id
        self.redeemed = redeemed
        self.shop_id = shop_id
        self.price = price
        self.note = note
        self.tags = tags
        self.execute()

    def execute(self):
        # verify input data

        n = len(self.game_id)

        if (self.redeemed is None or n != len(self.redeemed)):
            print(
                f'Error: Parameter \'{nameof(self.redeemed)}\' length mismatch: exiting')
            return

        if (self.shop_id is not None and n != len(self.shop_id)):
            print(
                f'Error: Parameter \'{nameof(self.shop_id)}\' length mismatch: ommiting')
            self.shop_id = None

        if (self.price is not None and n != len(self.price)):
            print(
                f'Error: Parameter \'{nameof(self.price)}\' length mismatch: ommiting')
            self.price = None

        if (self.note is not None and n != len(self.note)):
            print(
                f'Error: Parameter \'{nameof(self.note)}\' length mismatch: ommiting')
            self.note = None

        if (self.tags is not None and n != len(self.tags)):
            print(
                f'Error: Parameter \'{nameof(self.tags)}\' length mismatch: ommiting')
            self.tags = None

        # define & request data
        method = 'POST'
        endpoint = 'collection/copies/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = pandas.DataFrame({'gameId': self.game_id,
                                 'redeemed':  self.redeemed,
                                 'shop':  self.shop_id,
                                 'price':  self.price,
                                 'note':  self.note,
                                 'tags':  self.tags}
                                ).to_dict(orient='records')

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADUpdateCopiesFromGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-patch

    def __init__(self, copies_id, redeemed=None, shop_id=None, price=None, copies_note=None, copies_tags=None):
        self.copies_id = copies_id
        self.redeemed = redeemed
        self.shop_id = shop_id
        self.price = price
        self.copies_note = copies_note
        self.copies_tags = copies_tags
        self.execute()

    def execute(self):
        # verify input data
        n = len(self.copies_id)

        if (self.redeemed is None or n != len(self.redeemed)):
            print(
                f'Error: Parameter \'{nameof(self.redeemed)}\' length mismatch: ommiting')
            self.redeemed = None

        if (self.shop_id is not None and n != len(self.shop_id)):
            print(
                f'Error: Parameter \'{nameof(self.shop_id)}\' length mismatch: ommiting')
            self.shop_id = None

        if (self.price is not None and n != len(self.price)):
            print(
                f'Error: Parameter \'{nameof(self.price)}\' length mismatch: ommiting')
            self.price = None

        if (self.copies_note is not None and n != len(self.copies_note)):
            print(
                f'Error: Parameter \'{nameof(self.copies_note)}\' length mismatch: ommiting')
            self.copies_note = None

        if (self.copies_tags is not None and n != len(self.copies_tags)):
            print(
                f'Error: Parameter \'{nameof(self.copies_tags)}\' length mismatch: ommiting')
            self.copies_tags = None

        # define & request data
        method = 'PATCH'
        endpoint = 'collection/copies/v1'
        security = 'oa2'
        params = {}
        header = {}

        body = pandas.DataFrame({'id': self.copies_id,
                                 'redeemed':  self.redeemed,
                                 'shop':  self.shop_id,
                                 'price':  pandas.DataFrame({'amount': self.price,
                                                             'currency':  'EUR'}
                                                            ).to_dict(orient='records'),
                                 'note':  self.copies_note,
                                 'tags':  self.copies_tags}
                                ).to_dict(orient='records')

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADDeleteCopies:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-delete

    def __init__(self, copies_id):
        self.copies_id = copies_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'DELETE'
        endpoint = 'collection/copies/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.copies_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADGetCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'collection/groups/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)
            self.categories_id = self.df['id'].to_list()
            self.categories_title = self.df['title'].to_list()
            self.categories_is_public = self.df['public'].to_list()


class ITADCreateNewCategory:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-post

    def __init__(self, category_title, category_public):
        self.category_title = category_title
        self.category_public = category_public
        self.execute()

    def execute(self):
        # define & request data
        method = 'POST'
        endpoint = 'collection/groups/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = {'title': self.category_title,
                'public': self.category_public}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.created_category_id = self.response['id']
            self.created_category_title = self.response['title']
            self.created_category_public = self.response['public']


class ITADUpdateCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-patch

    def __init__(self, categories_update_id, categories_update_title, categories_update_is_public, categories_update_position):
        self.categories_update_id = categories_update_id
        self.categories_update_title = categories_update_title
        self.categories_update_is_public = categories_update_is_public
        self.categories_update_position = categories_update_position
        self.execute()

    def execute(self):
        n = len(self.categories_update_id)
        if (n != len(self.categories_update_title)):
            print('Parameter length mismatch, parameter ommited')
            self.categories_update_title = None
        if (n != len(self.categories_update_is_public)):
            print('Parameter length mismatch, parameter ommited')
            self.categories_update_is_public = None
        if (n != len(self.categories_update_position)):
            print('Parameter length mismatch, parameter ommited')
            self.categories_update_position = None

        # define & request data
        method = 'PATCH'
        endpoint = 'collection/groups/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = pandas.DataFrame({'id': self.categories_update_id,
                                 'title':  self.categories_update_title,
                                 'public':  self.categories_update_is_public,
                                 'position':  self.categories_update_position}
                                ).to_dict(orient='records')

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)
            self.categories_id = self.df['id'].to_list()
            self.categories_title = self.df['title'].to_list()
            self.categories_is_public = self.df['public'].to_list()


class ITADDeleteCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-delete

    def __init__(self, categories_ids_to_delete):
        self.categories_ids_to_delete = categories_ids_to_delete
        self.execute()

    def execute(self):
        # define & request data
        method = 'DELETE'
        endpoint = 'collection/groups/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.categories_ids_to_delete

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADGetUserInfo:
    # https://docs.isthereanydeal.com/#tag/User/operation/user-info-v2

    def __init__(self):
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'user/info/v2'
        security = 'oa2'
        params = {}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.username = self.response['username']


class ITADGetUserNotes:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # define & request data
        method = 'GET'
        endpoint = 'user/notes/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = {}

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)

        # process response data
        if self.response_code == 200:
            self.df = pandas.DataFrame(self.response)
            self.found_games_id = self.df['gid'].to_list()
            self.found_notes = self.df['note'].to_list()


class ITADPutUserNotesToGame:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-put

    def __init__(self, games_id, games_note):
        self.games_id = games_id
        self.games_note = games_note
        self.execute()

    def execute(self):
        if (len(self.games_id) != len(self.games_note)):
            print('Parameter length mismatch, parameter ommited')
            return

        # define & request data
        method = 'PUT'
        endpoint = 'user/notes/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = pandas.DataFrame({'gid': self.games_id,
                                 'note':  self.games_note}
                                ).to_dict(orient='records')

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


class ITADDelUserNotesFromGame:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # define & request data
        method = 'DELETE'
        endpoint = 'user/notes/v1'
        security = 'oa2'
        params = {}
        header = {}
        body = self.games_id

        self.response_code, self.response = send_request(method=method,
                                                         endpoint=endpoint,
                                                         security=security,
                                                         params=params,
                                                         header=header,
                                                         body=body)


if __name__ == '__main__':
    # # Clear console on Windows
    # if os.name == 'nt':
    #     os.system('cls')

    access_token = get_access_token()

    # ==================== EXAMPLE GAMES ====================

    # 018d937f-3a3b-7210-bd2d-0d1dfb1d84c0 https://isthereanydeal.com/game/red-dead-redemption-2/info/
    # 018d937f-5233-732a-9727-ab9b4d72c304 https://isthereanydeal.com/game/final-fantasy/info/
    #
    # 018d937f-5024-7396-b919-616080c759a4 view-source:https://isthereanydeal.com/game/the-ramp/info/
    # 018d937f-2950-736f-bf13-1833d2fcd8af https://isthereanydeal.com/game/cypher/info/

    # ==================== SEARCH GAMES & INFO ====================

    x1 = ITADSearchGames(game_title_to_search='teken',
                         max_results=10)
    print('')
    print(f'{x1.found_games_number} games found games for: {x1.game_title_to_search}')
    print(x1.found_games_title)

    x2 = ITADGetGameInfo(game_id='018d937f-6ef1-73d9-ad41-390d2d748c30')
    print('')
    print(f'game info for {x2.game_id}')
    print(f'game info for {x2.game_title}')

    # ==================== WAITLIST  ====================

    x3 = ITADGetGamesFromWaitlist()
    print(x3.waitlist_games_title[1:5])

    x4 = ITADPutGamesIntoWaitlist(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                   '018d937f-5233-732a-9727-ab9b4d72c304'])

    x5 = ITADDelGamesFromWaitlist(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                   '018d937f-5233-732a-9727-ab9b4d72c304'])

    # ==================== COLLECTION ====================
    # x6 = ITADGetGamesFromCollection()
    # print(x6.collection_games_title[1:5])

    # x7 = ITADPutGamesIntoCollection(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                                  '018d937f-5233-732a-9727-ab9b4d72c304'])

    # x8 = ITADDelGamesFromCollection(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                                  '018d937f-5233-732a-9727-ab9b4d72c304'])

    # COPIES
    # x9 = ITADGetCopiesOfGames(['018d937f-5024-7396-b919-616080c759a4',
    #                            '018d937f-2950-736f-bf13-1833d2fcd8af',
    #                            '018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                            '018d937f-5233-732a-9727-ab9b4d72c304'])
    # print(x9.df)

    # x10 = ITADAddCopiesToGames(game_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                                     '018d937f-5233-732a-9727-ab9b4d72c304'],
    #                            redeemed=[True,
    #                                      True],
    #                            shop_id=[2,
    #                                     2],
    #                            price=None,
    #                            note=None,
    #                            tags=None
    #                            )
    # x10 = ITADUpdateCopiesFromGames([182096370, 182096372],
    #                                 [False, True],
    #                                 [3, 3],
    #                                 [5, 6],
    #                                 ['tes note', 'test note 2'],
    #                                 [['tag1', 'tag2'], ['tag3', 'tag3']])

    # x9.execute()
    # print(x9.df)

    # x11 = ITADDeleteCopies([182096370, 182096372])

    # x9.execute()
    # print(x9.df)

    # ==================== CATERORIES ====================
    # x13 = ITADGetCategories()
    # print(x13.df, '\n')

    # x14 = ITADCreateNewCategory('new_category2', False)
    # print(x14.df)

    # x15 = ITADUpdateCategories(categories_update_id=[15199, 15200, 15201],
    #                            categories_update_title=['a', 'b', 'c'],
    #                            categories_update_is_public=[
    #                                False, False, False],
    #                            categories_update_position=[99, 99, 99])
    # print('\n', x15.df, '\n')

    # x16 = ITADDeleteCategories([15177])

    # ==================== USER ====================
    # x17 = ITADGetUserInfo()
    # print(x17.username)

    # x18 = ITADGetUserNotes()
    # print(x18.df)

    # x19 = ITADPutUserNotesToGame(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                                        '018d937f-5233-732a-9727-ab9b4d72c304'],
    #                              games_note=['bb',
    #                                          'cc'])

    # x20 = ITADDelUserNotesFromGame(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
    #                                 '018d937f-5233-732a-9727-ab9b4d72c304'])

    pass
