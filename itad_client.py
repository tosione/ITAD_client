
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
MSG_PARAM_WRONG_LEN = 'Parameter lenght mismatch'
MSG_PARAM_NONE = 'Parameter missing'


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

    # prepare data
    header['Content-Type'] = 'application/json'

    if security == 'key':
        params['key'] = API_KEY
    elif security == 'oa2':
        header['Authorization'] = 'Bearer ' + access_token
    else:
        raise ValueError('Invalid security type: valid ''key'' or ''oa2'' ')
        return 0, None

    if endpoint.startswith('http') or endpoint == "":
        raise ValueError('Endpoint contains full HTTP addres?')
        return 0, None
    else:
        url = BASE_URL + endpoint

    # make request
    if (method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
        resp = requests.request(method=method,
                                url=url,
                                headers=header,
                                params=params,
                                json=body)
        if resp.status_code >= 400:
            # handle request error
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


def len_opt_arg(x, n):
    return x is None or len(x) == n


def len_oblig_arg(x, n):
    return len(x) == n


def print_list_vert(x):
    print(*x, sep='\n')


class ITADSearchGames:
    # https://docs.isthereanydeal.com/#tag/Lookup/operation/games-search-v1

    def __init__(self, game_title_to_search, max_results=None):
        self.game_title_to_search = game_title_to_search
        self.max_results = max_results
        self.execute()

    def execute(self):
        # verify input data
        assert self.game_title_to_search is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='games/search/v1',
                                                 security='key',
                                                 params={'title': self.game_title_to_search,
                                                         'results': self.max_results},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.found_games_id = self.df['id'].to_list()
                self.found_games_slug = self.df['slug'].to_list()
                self.found_games_title = self.df['title'].to_list()
                self.found_games_type = self.df['type'].to_list()
                self.found_game_mature = self.df['mature'].to_list()
                self.found_games_assets = self.df['assets'].to_list()
                self.found_games_number = len(self.found_games_id)
            else:
                self.found_games_id = []
                self.found_games_slug = []
                self.found_games_title = []
                self.found_games_type = []
                self.found_game_mature = []
                self.found_games_assets = []
                self.found_games_number = 0


class ITADGetGameInfo:
    # https://docs.isthereanydeal.com/#tag/Game/operation/games-info-v2

    def __init__(self, game_id):
        self.game_id = game_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.game_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='games/info/v2',
                                                 security='key',
                                                 params={'id': self.game_id},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.game_info = self.resp

            # put some of the info into variables
            self.game_slug = self.resp['slug']
            self.game_title = self.resp['title']
            self.game_type = self.resp['type']
            self.game_app_id = self.resp['appid']
            self.game_urls = self.resp['urls']


def get_games_title(games_id):
    assert games_id is not None, MSG_PARAM_NONE
    assert type(games_id) is list
    titles = []
    for gid in games_id:
        # make request
        resp_code, resp = send_request(method='GET',
                                       endpoint='games/info/v2',
                                       security='key',
                                       params={'id': gid},
                                       header={},
                                       body={}
                                       )
        # process response data
        if resp_code == 200:
            titles.append(resp['title'])
        else:
            titles.append(None)
    return titles


def get_game_title(game_id):
    # make request
    resp_code, resp = send_request(method='GET',
                                   endpoint='games/info/v2',
                                   security='key',
                                   params={'id': game_id},
                                   header={},
                                   body={}
                                   )
    # process response data
    if resp_code == 200:
        return resp['title']
    else:
        return None


class ITADGetGamesFromWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='waitlist/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.waitlist_games_id = self.df['id'].to_list()
                self.waitlist_games_slug = self.df['slug'].to_list()
                self.waitlist_games_title = self.df['title'].to_list()
                self.waitlist_games_assets = self.df['assets'].to_list()
                self.waitlist_games_is_mature = self.df['mature'].to_list()
                self.waitlist_games_date_added = self.df['added'].to_list()
                self.waitlist_games_number = len(self.waitlist_games_id)
            else:
                self.waitlist_games_id = []
                self.waitlist_games_slug = []
                self.waitlist_games_title = []
                self.waitlist_games_assets = []
                self.waitlist_games_is_mature = []
                self.waitlist_games_date_added = []
                self.waitlist_games_number = 0


class ITADPutGamesIntoWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-put

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='PUT',
                                                 endpoint='waitlist/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )


class ITADDelGamesFromWaitlist:
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='DELETE',
                                                 endpoint='waitlist/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )


class ITADGetGamesFromCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='collection/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.collection_games_id = self.df['id'].to_list()
                self.collection_games_slug = self.df['slug'].to_list()
                self.collection_games_title = self.df['title'].to_list()
                self.collection_games_assets = self.df['assets'].to_list()
                self.collection_games_is_mature = self.df['mature'].to_list()
                self.collection_games_date_added = self.df['added'].to_list()
                self.collection_games_number = len(self.collection_games_id)
            else:
                self.collection_games_id = []
                self.collection_games_slug = []
                self.collection_games_title = []
                self.collection_games_assets = []
                self.collection_games_is_mature = []
                self.collection_games_date_added = []
                self.collection_games_number = 0


class ITADPutGamesIntoCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-put

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='PUT',
                                                 endpoint='collection/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )


class ITADDelGamesFromCollection:
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='DELETE',
                                                 endpoint='collection/games/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )


class ITADGetCopiesOfGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-get

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='collection/copies/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.games = pandas.DataFrame(self.df['game'].to_list())

                # replace None shops with dictionaries of None values
                # to avoid exception with DataFrame
                shop_list = [{'id': None, 'Name': None}
                             if shop is None else shop for shop in self.df['shop'].to_list()]
                self.shops = pandas.DataFrame(shop_list)

                self.copies_id = self.df['id'].to_list()
                self.copies_game_id = self.games['id'].to_list()
                self.copies_shop_id = self.shops['id'].to_list()
                self.copies_shop_name = self.shops['name'].to_list()
                self.copies_shop = self.df['shop'].to_list()
                self.copies_redeemed = self.df['redeemed'].to_list()
                self.copies_price = self.df['price'].to_list()
                self.copies_note = self.df['note'].to_list()
                self.copies_tags = self.df['tags'].to_list()
                self.copies_date_added = self.df['added'].to_list()
                self.copies_number = len(self.copies_game_id)

            else:
                self.copies_id = None
                self.copies_game_id = None
                self.copies_shop_id = None
                self.copies_shop_name = None
                self.copies_shop = None
                self.copies_redeemed = None
                self.copies_price = None
                self.copies_note = None
                self.copies_tags = None
                self.copies_date_added = None
                self.copies_number = 0


class ITADAddCopiesToGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-post

    def __init__(self, copies_game_id, copies_redeemed, copies_shop_id=None, copies_price_eur=None, copies_note=None, copies_tags=None):
        self.copies_game_id = copies_game_id
        self.copies_redeemed = copies_redeemed
        self.copies_shop_id = copies_shop_id
        self.copies_price_eur = copies_price_eur
        self.copies_note = copies_note
        self.copies_tags = copies_tags
        self.execute()

    def execute(self):
        # verify input data
        assert self.copies_game_id is not None, MSG_PARAM_NONE
        assert self.copies_redeemed is not None, MSG_PARAM_NONE

        n = len(self.copies_game_id)
        assert len_oblig_arg(self.copies_redeemed, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_shop_id, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_price_eur, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_note, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_tags, n), MSG_PARAM_WRONG_LEN

        # prepare {prices, currency} from prices_eur
        if self.copies_price_eur is None:
            self.copies_prices = [None for _ in range(n)]
        else:
            self.copies_prices = [None if price is None else {
                'amount': price, 'currency':  'EUR'} for price in self.copies_price_eur]

        # make request
        self.resp_code, self.resp = send_request(method='POST',
                                                 endpoint='collection/copies/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=pandas.DataFrame({'gameId': self.copies_game_id,
                                                                        'redeemed':  self.copies_redeemed,
                                                                        'shop': self.copies_shop_id,
                                                                        'price': self.copies_prices,
                                                                        'note':  self.copies_note,
                                                                        'tags':  self.copies_tags}
                                                                       ).to_dict(orient='records')
                                                 )


# ===============================================================================================

class ITADUpdateCopiesFromGames:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-patch

    def __init__(self, copies_id, copies_redeemed=None, copies_shop_id=None, copies_price_eur=None, copies_note=None, copies_tags=None):
        self.copies_id = copies_id
        self.copies_redeemed = copies_redeemed
        self.copies_shop_id = copies_shop_id
        self.copies_price_eur = copies_price_eur
        self.copies_note = copies_note
        self.copies_tags = copies_tags
        self.execute()

    def execute(self):
        # verify input data
        assert self.copies_id is not None, MSG_PARAM_NONE

        n = len(self.copies_id)
        assert len_opt_arg(self.copies_redeemed, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_shop_id, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_price_eur, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_note, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.copies_tags, n), MSG_PARAM_WRONG_LEN

        # prepare {prices, currency} from prices_eur
        if self.copies_price_eur is None:
            self.copies_prices = [None for _ in range(n)]
        else:
            self.copies_prices = [None if price is None else {
                'amount': price, 'currency':  'EUR'} for price in self.copies_price_eur]

        # make request
        self.resp_code, self.resp = send_request(method='PATCH',
                                                 endpoint='collection/copies/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=pandas.DataFrame({'id': self.copies_id,
                                                                        'redeemed': self.copies_redeemed,
                                                                        'shop': self.copies_shop_id,
                                                                        'price': self.copies_prices,
                                                                        'note': self.copies_note,
                                                                        'tags': self.copies_tags}
                                                                       ).to_dict(orient='records')
                                                 )


class ITADDeleteCopies:
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-delete

    def __init__(self, copies_id):
        self.copies_id = copies_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.copies_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='DELETE',
                                                 endpoint='collection/copies/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.copies_id
                                                 )


class ITADGetCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='collection/groups/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.categories_id = self.df['id'].to_list()
                self.categories_title = self.df['title'].to_list()
                self.categories_public = self.df['public'].to_list()
            else:
                self.categories_id = None
                self.categories_title = None
                self.categories_public = None


class ITADCreateNewCategory:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-post

    def __init__(self, category_title, category_public):
        self.category_title = category_title
        self.category_public = category_public
        self.execute()

    def execute(self):
        # verify input data
        assert self.category_title is not None, MSG_PARAM_NONE
        assert self.category_public is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='POST',
                                                 endpoint='collection/groups/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={'title': self.category_title,
                                                       'public': self.category_public}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.created_category_id = self.resp['id']
            self.created_category_title = self.resp['title']
            self.created_category_public = self.resp['public']


class ITADUpdateCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-patch

    def __init__(self, categories_upd_id, categories_upd_title, categories_upd_public, categories_upd_position):
        self.categories_upd_id = categories_upd_id
        self.categories_upd_title = categories_upd_title
        self.categories_upd_public = categories_upd_public
        self.categories_upd_position = categories_upd_position
        self.execute()

    def execute(self):
        # verify input data
        assert self.categories_upd_id is not None, MSG_PARAM_NONE

        n = len(self.categories_upd_id)
        assert len_opt_arg(self.categories_upd_title, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.categories_upd_public, n), MSG_PARAM_WRONG_LEN
        assert len_opt_arg(self.categories_upd_position,
                           n), MSG_PARAM_WRONG_LEN

        # prepare data

        # make request
        self.resp_code, self.resp = send_request(method='PATCH',
                                                 endpoint='collection/groups/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=pandas.DataFrame({'id': self.categories_upd_id,
                                                                        'title':  self.categories_upd_title,
                                                                        'public':  self.categories_upd_public,
                                                                        'position':  self.categories_upd_position}
                                                                       ).to_dict(orient='records')
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.categories_id = self.df['id'].to_list()
                self.categories_title = self.df['title'].to_list()
                self.categories_public = self.df['public'].to_list()
            else:
                self.categories_id = None
                self.categories_title = None
                self.categories_public = None


class ITADDeleteCategories:
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-delete

    def __init__(self, categories_id_to_delete):
        self.categories_id_to_delete = categories_id_to_delete
        self.execute()

    def execute(self):
        # verify input data
        assert self.categories_id_to_delete is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='DELETE',
                                                 endpoint='collection/groups/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.categories_id_to_delete
                                                 )


class ITADGetUserInfo:
    # https://docs.isthereanydeal.com/#tag/User/operation/user-info-v2

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='user/info/v2',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.username = self.resp['username']


class ITADGetUserNotes:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.resp_code, self.resp = send_request(method='GET',
                                                 endpoint='user/notes/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body={}
                                                 )

        # process response data
        if self.resp_code == 200:
            self.df = pandas.DataFrame(self.resp)
            if not self.df.empty:
                self.found_games_id = self.df['gid'].to_list()
                self.found_notes = self.df['note'].to_list()
            else:
                self.found_games_id = None
                self.found_notes = None


class ITADPutUserNotesToGame:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-put

    def __init__(self, games_id, games_note):
        self.games_id = games_id
        self.games_note = games_note
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE
        assert self.games_note is not None, MSG_PARAM_NONE

        n = len(self.games_id)
        assert len_oblig_arg(self.games_note, n), MSG_PARAM_WRONG_LEN

        # make request
        self.resp_code, self.resp = send_request(method='PUT',
                                                 endpoint='user/notes/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=pandas.DataFrame({'gid': self.games_id,
                                                                        'note':  self.games_note}
                                                                       ).to_dict(orient='records')
                                                 )


class ITADDelUserNotesFromGame:
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-delete

    def __init__(self, games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.resp_code, self.resp = send_request(method='DELETE',
                                                 endpoint='user/notes/v1',
                                                 security='oa2',
                                                 params={},
                                                 header={},
                                                 body=self.games_id
                                                 )


if __name__ == '__main__':
    # # Clear console on Windows
    # if os.name == 'nt':
    #     os.system('cls')

    access_token = get_access_token()

    # ==================== EXAMPLE GAMES ====================
    #
    # 018d937f-3a3b-7210-bd2d-0d1dfb1d84c0 https://isthereanydeal.com/game/red-dead-redemption-2/info/
    # 018d937f-5233-732a-9727-ab9b4d72c304 https://isthereanydeal.com/game/final-fantasy/info/
    #
    # 018d937f-5024-7396-b919-616080c759a4 view-source:https://isthereanydeal.com/game/the-ramp/info/
    # 018d937f-2950-736f-bf13-1833d2fcd8af https://isthereanydeal.com/game/cypher/info/

    debug_parts = {'game_info': False,
                   'waitlist': False,
                   'collection': False,
                   'copies': True,
                   'categories': False,
                   'user': False
                   }

    # ==================== SEARCH GAMES & INFO ====================
    if debug_parts['game_info']:

        x1 = ITADSearchGames(game_title_to_search='teken',
                             max_results=10)
        print(
            f'\n{x1.found_games_number} games found games for: {x1.game_title_to_search}')
        print(x1.found_games_title)

        x2 = ITADGetGameInfo(game_id='018d937f-6ef1-73d9-ad41-390d2d748c30')
        print(f'\nGame ID: {x2.game_id}')
        print(f'Game title: {x2.game_title}')
        print('More info with \'game_info\' variable')

        ids = ['018d937f-5024-7396-b919-616080c759a4',
               '018d937f-2950-736f-bf13-1833d2fcd8af',
               '018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
               '018d937f-5233-732a-9727-ab9b4d72c304']
        titles = get_games_title(games_id=ids)
        print('\nSearch titles for various Games ID')
        print(pandas.DataFrame({'ID': ids, 'titles': titles}))

        id = '018d937f-3a3b-7210-bd2d-0d1dfb1d84c0'
        title = get_game_title(game_id=id)
        print('\nSearch titles for one Game ID')
        print(id)
        print(title)

    # ==================== WAITLIST  ====================
    if debug_parts['waitlist']:

        x3 = ITADGetGamesFromWaitlist()
        print(f'\n{x3.waitlist_games_number} games in Wailist, showwing 1-10:')
        print(x3.waitlist_games_title[0:10])

        x4 = ITADPutGamesIntoWaitlist(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                                '018d937f-5233-732a-9727-ab9b4d72c304'])
        print(f'\nAdded {len(x4.games_id)} games to waitlist')
        x3.execute()
        print(f'\n{x3.waitlist_games_number} games in Wailist')

        x5 = ITADDelGamesFromWaitlist(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                                '018d937f-5233-732a-9727-ab9b4d72c304'])
        print(f'\nRemoved {len(x5.games_id)} games from waitlist')
        x3.execute()
        print(f'\n{x3.waitlist_games_number} games in Wailist.')

    # ==================== COLLECTION ====================
    if debug_parts['collection']:
        x6 = ITADGetGamesFromCollection()
        print(f'\n{x6.collection_games_number} games in collection, showwing 1-10:')
        print(x6.collection_games_title[0:10])

        x7 = ITADPutGamesIntoCollection(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                                  '018d937f-5233-732a-9727-ab9b4d72c304'])
        print(f'\nAdded {len(x7.games_id)} games to collection')
        x6.execute()
        print(f'\n{x6.collection_games_number} games in collection')

        x8 = ITADDelGamesFromCollection(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                                  '018d937f-5233-732a-9727-ab9b4d72c304'])
        print(f'\nRemoved {len(x8.games_id)} games from collection')
        x6.execute()
        print(f'\n{x6.collection_games_number} games in collection')

    # ==================== COPIES ====================
    if debug_parts['copies']:
        x9 = ITADGetCopiesOfGames(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                            '018d937f-5233-732a-9727-ab9b4d72c304'])
        print(f'\n{x9.copies_number} copies found:')
        print(x9.df)

        # x10 = ITADAddCopiesToGames(copies_game_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0', '018d937f-5233-732a-9727-ab9b4d72c304'],
        #                            copies_redeemed=[True, True],
        #                            copies_shop_id=None,
        #                            copies_price_eur=None,
        #                            copies_note=None,
        #                            copies_tags=None
        #                            )
        # print(f'\n{len(x10.copies_game_id)} copies added to games:')
        # print(pandas.DataFrame({'Copies': x10.copies_game_id}))
        # x9.execute()
        # print(f'\n{x9.copies_number} copies found:')
        # print(x9.df)

        # x10 = ITADUpdateCopiesFromGames(copies_id=[182131346, 182131381],
        #                                 copies_redeemed=[False, True],
        #                                 copies_shop_id=[3, 3],
        #                                 copies_price_eur=[5, 6],
        #                                 copies_note=['note x', 'note 2'],
        #                                 copies_tags=[['tag1', 'tag2'], ['tag3', 'tag3']])
        # x9.execute()
        # print(f'\n{x9.copies_number} copies found:')
        # print(x9.df)

        # x11 = ITADDeleteCopies(copies_id=x9.copies_id)
        # print(f'\nDeleted copies with ID:')
        # print_list_vert(x11.copies_id)
        # x9.execute()
        # print(f'\n{x9.copies_number} copies found:')
        # print(x9.df)

    # ==================== CATERORIES ====================
    if debug_parts['categories']:
        x13 = ITADGetCategories()
        print('\nAll categories:')
        print(x13.df)

        x14 = ITADCreateNewCategory(category_title='new_category2',
                                    category_public=False)
        print('\nAdded a new category:')
        print(f'ID={x14.created_category_id}')
        print(f'Title={x14.created_category_title}')
        print(f'Public={x14.created_category_public}')

        x15 = ITADUpdateCategories(categories_update_id=[15199, 15200, 15201],
                                   categories_update_title=['a', 'b', 'c'],
                                   categories_update_public=[
                                       False, False, False],
                                   categories_update_position=[99, 99, 99])
        print(f'\nUpdated {len(x15.categories_upd_id)} categories')
        print(x15.df)

        x16 = ITADDeleteCategories([15177])
        print(f'\nDeleted {len(x16.categories_id_to_delete)} categories')
        print(x15.df)

    # ==================== USER ====================
    if debug_parts['user']:
        x17 = ITADGetUserInfo()
        print(x17.username)

        x18 = ITADGetUserNotes()
        print(x18.df)

        x19 = ITADPutUserNotesToGame(games_id=['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                               '018d937f-5233-732a-9727-ab9b4d72c304'],
                                     games_note=['bb',
                                                 'cc'])

        x20 = ITADDelUserNotesFromGame(['018d937f-3a3b-7210-bd2d-0d1dfb1d84c0',
                                        '018d937f-5233-732a-9727-ab9b4d72c304'])

    pass
