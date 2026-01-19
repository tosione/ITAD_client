"""
IsThereAnyDeal (ITAD) API client using OAuth2 and API Key.

This module provides a client for interacting with the IsThereAnyDeal
(ITAD) API. It supports OAuth2 authentication for personal data and API
key authentication for non-personal data.

The client allows you to perform various operations such as retrieving
user information, searching for games, managing collections, managing
waitlists, and more. It provides high-level functions for making API
requests and handling authentication.

Classes:
    ITADBaseClass: Base class for all ITAD client classes.
        - get_access_token: loads from JSON or obtains new tokens.
        - get_new_tokens_from_itad: obtains new tokens.
        - test_oauth_session: tests the OAuth2 session.
        - send_request: sends data a request to ITAD.
        - get_games_title: retrieves the titles of multiple games.
        - get_game_title: retrieves the title of a single game.
        - get_game_url: gets the URL of a game.
        - get_games_url: gets the URLs of multiple games.
        - save_json: Saves JSON data to a file.
        - load_json: Loads JSON data from a file.
    ITADSearchGames
    ITADGetGameInfo
    ITADGetGamesFromWaitlist
    ITADPutGamesIntoWaitlist
    ITADDeleteGamesFromWaitlist
    ITADGetGamesFromCollection
    ITADPutGamesIntoCollection
    ITADDelGamesFromCollection
    ITADGetCopiesOfGames
    ITADAddCopiesToGames
    ITADUpdateCopiesOfGames
    ITADDeleteCopiesOfGames
    ITADGetCategories
    ITADCreateNewCategory
    ITADUpdateCategories
    ITADDeleteCategories
    ITADGetUserInfo
    ITADGetUserNotes
    ITADPutUserNotesFromGame
    ITADDeleteUserNotesFromGame
    ITADGetShopsInfo

This module uses the `requests_oauthlib` library for OAuth2 authentication
and the `print_color` library for colored printing.

For privacy reasons, the API_KEY, CLIENT_ID, and CLIENT_SECRET are
stored in the `private_data.py` module. User must generate its own
`private_data.py` were this constants must be defined.

For more information on the ITAD API, refer to the official
documentation: https://docs.isthereanydeal.com/

Author: tosione
"""

__version__ = '1.0'
__author__ = 'tosione'

# Standard library imports
import os
import webbrowser
import json
from datetime import datetime
import pandas
from pandas import DataFrame

# Related third party imports
import requests
import requests_oauthlib
import print_color

# Local application/library specific imports
import private_data

# Constants
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
MSG_PARAM_NONE = 'Parameter is None'
MSG_PARAM_EMPTY = 'Parameter is empty'


# ==================== Base class ====================
class ITADBaseClass:
    @classmethod
    def get_access_token(cls, api_key, client_id, client_secret):
        # Create an OAuth2 Session
        """
        Get an access token to use with the ITAD API.

        First, try to load existing tokens from a JSON file.
        If the file does not exist, obtain new tokens using the PKCE flow.
        Save the new tokens to the same JSON file.
        If the tokens are valid, return the access token.
        Otherwise, return None.
        """
        cls.api_key = api_key
        cls.client_id = client_id
        cls.client_secret = client_secret
        cls.oauth_session = requests_oauthlib.OAuth2Session(client_id=cls.client_id,
                                                            redirect_uri=REDIRECT_URI,
                                                            scope=SCOPE,
                                                            pkce='S256')

        if os.path.exists(TOKEN_FILE):
            cls.oauth_session.token = cls.load_json(TOKEN_FILE)
            cls.oauth_session.refresh_token(token_url=TOKEN_URL,
                                            auth=(cls.client_id, cls.client_secret))
            cls.save_json(TOKEN_FILE, cls.oauth_session.token)
        else:
            cls.get_new_tokens_from_itad()
            cls.save_json(TOKEN_FILE, cls.oauth_session.token)
            print_ok(f'Created new tokens to file ({TOKEN_FILE})')

        if cls.test_oauth_session():
            cls.access_token = cls.oauth_session.token['access_token']
        else:
            cls.access_token = None

    @classmethod
    def get_new_tokens_from_itad(cls):

        # Step 1: obtain authorization URL
        auth_url, auth_state = cls.oauth_session.authorization_url(AUTH_URL)

        # Step 2: open URL in browser, ask user to authorize and copy redirect URL
        print('Please go to this URL and authorize access:')
        print(auth_url)
        webbrowser.open(auth_url)

        # Step 3: Get the authorization verifier code from the callback url
        redirect_URL = input('\nPaste the full redirect URL here: ')

        # Step 4: Fetch the access token
        cls.oauth_session.fetch_token(
            TOKEN_URL, authorization_response=redirect_URL)

        print('Tokens expires in ',
              cls.oauth_session.token['expires_in']/3600/24, ' days')
        print('Tokens expires at ',
              datetime.fromtimestamp(cls.oauth_session.token['expires_at']))

    @classmethod
    def test_oauth_session(cls):
        ok = cls.oauth_session.get(
            BASE_URL + 'user/info/v2').status_code == 200
        if ok:
            print_ok('OAuth is working')
        else:
            print_err('OAuth is not working')
        return ok

    @classmethod
    def send_request(cls, method, endpoint, security, params={}, header={}, body={}):
        """
        Send a request to the ITAD API.

        Parameters
        ----------
        method : str
            The HTTP method to use. Valid values are 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'.
        endpoint : str
            The API endpoint to use. If it contains the full HTTP address, raise a ValueError.
        security : str
            The security type to use. Valid values are 'key' or 'oa2'.
        params : dict, optional
            The query parameters to use.
        header : dict, optional
            The headers to use.
        body : dict, optional
            The JSON body data to send.

        Returns
        -------
        status_code : int
            The HTTP status code of the response.
        response : dict
            The JSON data of the response. If the response was empty, return None.
        """

        # prepare data
        header['Content-Type'] = 'application/json'

        if security == 'key':
            params['key'] = cls.api_key
        elif security == 'oa2':
            header['Authorization'] = 'Bearer ' + cls.access_token
        else:
            raise ValueError(
                'Invalid security type: valid ''key'' or ''oa2'' ')

        if endpoint.startswith('http') or endpoint == "":
            raise ValueError('Endpoint contains full HTTP addres?')
        else:
            url = BASE_URL + endpoint

        # make request
        if (method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
            resp_msg = requests.request(method=method,
                                        url=url,
                                        headers=header,
                                        params=params,
                                        json=body)
            cls.resp_code = resp_msg.status_code

            if resp_msg.status_code >= 400:
                # handle request error
                print_err(
                    f'HTTP error code({resp_msg.status_code}): {resp_msg.reason}. {resp_msg.json()['reason_phrase']}')
                if 'details' in resp_msg.json():
                    print_err(f'\tDetails: {resp_msg.json()['details']}')

                cls.resp = None
            elif resp_msg.content == b'':
                cls.resp = None  # request ok with empty response
            else:
                cls.resp = resp_msg.json()   # request ok
        else:
            print_err('Invalid HTTP method')
            cls.resp_code = 0
            cls.resp = None

    @classmethod
    def get_games_title(cls, games_id):
        assert games_id is not None, MSG_PARAM_NONE
        assert type(games_id) is list
        titles = []
        for gid in games_id:
            # make request
            cls.send_request(method='GET',
                             endpoint='games/info/v2',
                             security='key',
                             params={'id': gid},
                             header={},
                             body={}
                             )
            # process response data
            if cls.resp_code == 200:
                titles.append(cls.resp['title'])
            else:
                titles.append(None)
        return titles

    @classmethod
    def get_game_title(cls, game_id):
        # make request
        cls.send_request(method='GET',
                         endpoint='games/info/v2',
                         security='key',
                         params={'id': game_id},
                         header={},
                         body={}
                         )
        # process response data
        if cls.resp_code == 200:
            return cls.resp['title']
        else:
            return None

    @staticmethod
    def get_game_url(game_id, redirect=False):
        if redirect:
            # gets redirected address, takes longer
            return requests.get(f'https://isthereanydeal.com/game/id:{game_id}/').url
        else:
            return f'https://isthereanydeal.com/game/id:{game_id}/info/'

    @staticmethod
    def get_games_url(games_id, redirect=False):
        if redirect:
            # gets redirected addresses, takes longer
            return [requests.get(f'https://isthereanydeal.com/game/id:{game_id}/').url for game_id in games_id]
        else:
            return [f'https://isthereanydeal.com/game/id:{game_id}/info/' for game_id in games_id]

    @staticmethod
    def save_json(filename, data):
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4, check_circular=True)
        except Exception as e:
            print_err('Error saving JSON file:', e)

    @staticmethod
    def load_json(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print_err('Error loading JSON file:', e)
            return None


# ==================== Derived Classes ====================

class ITADSearchGames(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Lookup/operation/games-search-v1
    # https://docs.isthereanydeal.com/#tag/Game/operation/games-search-v1

    def __init__(self,
                 game_title_to_search,
                 max_results=None):
        self.game_title_to_search = game_title_to_search
        self.max_results = max_results
        self.execute()

    def execute(self):
        # verify input data
        assert self.game_title_to_search is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='GET',
                          endpoint='games/search/v1',
                          security='key',
                          params={'title': self.game_title_to_search,
                                  'results': self.max_results},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
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


class ITADGetGameInfo(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Game/operation/games-info-v2

    def __init__(self,
                 game_id):
        self.game_id = game_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.game_id is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='GET',
                          endpoint='games/info/v2',
                          security='key',
                          params={
                              'id': self.game_id},
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


class ITADGetGamesFromWaitlist(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.send_request(method='GET',
                          endpoint='waitlist/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
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


class ITADPutGamesIntoWaitlist(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-put

    def __init__(self,
                 games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE
        assert self.games_id is not [], MSG_PARAM_EMPTY

        # make request
        self.send_request(method='PUT',
                          endpoint='waitlist/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id
                          )


class ITADDeleteGamesFromWaitlist(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Waitlist-Games/operation/waitlist-games-v1-delete

    def __init__(self,
                 games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE
        assert self.games_id is not [], MSG_PARAM_EMPTY

        # make request
        self.send_request(method='DELETE',
                          endpoint='waitlist/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id
                          )


class ITADGetGamesFromCollection(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.send_request(method='GET',
                          endpoint='collection/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
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


class ITADPutGamesIntoCollection(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-put

    def __init__(self,
                 games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE
        assert self.games_id is not [], MSG_PARAM_EMPTY

        # make request
        self.send_request(method='PUT',
                          endpoint='collection/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id
                          )


class ITADDeleteGamesFromCollection(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Games/operation/collection-games-v1-delete

    def __init__(self,
                 games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE
        assert self.games_id is not [], MSG_PARAM_EMPTY

        # make request
        self.send_request(method='DELETE',
                          endpoint='collection/games/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id
                          )


class ITADGetCopiesOfGames(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-get
    # Description is wrong, it requieres Game IDs

    def __init__(self,
                 games_id_to_search):
        self.games_id_to_search = games_id_to_search
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id_to_search is not None, MSG_PARAM_NONE
        assert self.games_id_to_search is not [], MSG_PARAM_EMPTY

        # make request
        self.send_request(method='GET',
                          endpoint='collection/copies/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id_to_search
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
            if not self.df.empty:
                self.games = DataFrame(self.df['game'].to_list())

                # replace None shops with dictionaries of None values
                # to avoid exception with DataFrame
                shop_list = [{'id': None, 'name': None}
                             if shop is None else shop for shop in self.df['shop'].to_list()]
                self.shops = DataFrame(shop_list)

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


class ITADAddCopiesToGames(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-post
    # will also add games to collection if no already there

    def __init__(self,
                 copies_game_id,
                 copies_redeemed,
                 copies_shop_id=None,
                 copies_price_eur=None,
                 copies_note=None,
                 copies_tags=None):
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
        self.send_request(method='POST',
                          endpoint='collection/copies/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=DataFrame({'gameId': self.copies_game_id,
                                          'redeemed':  self.copies_redeemed,
                                          'shop': self.copies_shop_id,
                                          'price': self.copies_prices,
                                          'note':  self.copies_note,
                                          'tags':  self.copies_tags}
                                         ).to_dict(orient='records')
                          )


class ITADUpdateCopiesFromGames(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-patch

    def __init__(self,
                 copies_id,
                 copies_redeemed=None,
                 copies_shop_id=None,
                 copies_price_eur=None,
                 copies_note=None,
                 copies_tags=None):
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
        self.send_request(method='PATCH',
                          endpoint='collection/copies/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=DataFrame({'id': self.copies_id,
                                          'redeemed': self.copies_redeemed,
                                          'shop': self.copies_shop_id,
                                          'price': self.copies_prices,
                                          'note': self.copies_note,
                                          'tags': self.copies_tags}
                                         ).to_dict(orient='records')
                          )


class ITADDeleteCopies(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Copies/operation/collection-copies-v1-delete

    def __init__(self,
                 copies_id):
        self.copies_id = copies_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.copies_id is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='DELETE',
                          endpoint='collection/copies/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.copies_id
                          )


class ITADGetCategories(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.send_request(method='GET',
                          endpoint='collection/groups/v1',
                          security='oa2',
                          params={},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
            if not self.df.empty:
                self.categories_id = self.df['id'].to_list()
                self.categories_title = self.df['title'].to_list()
                self.categories_public = self.df['public'].to_list()
            else:
                self.categories_id = None
                self.categories_title = None
                self.categories_public = None


class ITADCreateNewCategory(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-post

    def __init__(self,
                 category_title,
                 category_public):
        self.category_title = category_title
        self.category_public = category_public
        self.execute()

    def execute(self):
        # verify input data
        assert self.category_title is not None, MSG_PARAM_NONE
        assert self.category_public is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='POST',
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


class ITADUpdateCategories(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-patch

    def __init__(self,
                 categories_upd_id,
                 categories_upd_title=None,
                 categories_upd_public=None,
                 categories_upd_position=None):
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
        self.send_request(method='PATCH',
                          endpoint='collection/groups/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=DataFrame({'id': self.categories_upd_id,
                                          'title':  self.categories_upd_title,
                                          'public':  self.categories_upd_public,
                                          'position':  self.categories_upd_position}
                                         ).to_dict(orient='records')
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
            if not self.df.empty:
                self.categories_id = self.df['id'].to_list()
                self.categories_title = self.df['title'].to_list()
                self.categories_public = self.df['public'].to_list()
            else:
                self.categories_id = None
                self.categories_title = None
                self.categories_public = None


class ITADDeleteCategories(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Collection-Groups/operation/collection-groups-v1-delete

    def __init__(self,
                 categories_del_id):
        self.categories_del_id = categories_del_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.categories_del_id is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='DELETE',
                          endpoint='collection/groups/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.categories_del_id
                          )


class ITADGetUserInfo(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/User/operation/user-info-v2

    def __init__(self):
        self.execute()

    def execute(self):
        pass
        # make request
        self.send_request(method='GET',
                          endpoint='user/info/v2',
                          security='oa2',
                          params={},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.username = self.resp['username']


class ITADGetUserNotes(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-get

    def __init__(self):
        self.execute()

    def execute(self):
        # make request
        self.send_request(method='GET',
                          endpoint='user/notes/v1',
                          security='oa2',
                          params={},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
            if not self.df.empty:
                self.found_games_id = self.df['gid'].to_list()
                self.found_notes = self.df['note'].to_list()
            else:
                self.found_games_id = None
                self.found_notes = None


class ITADPutUserNotesToGame(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-put

    def __init__(self,
                 games_id,
                 games_note):
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
        self.send_request(method='PUT',
                          endpoint='user/notes/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=DataFrame({'gid': self.games_id,
                                          'note':  self.games_note}
                                         ).to_dict(orient='records')
                          )


class ITADDeleteUserNotesFromGame(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/User-Notes/operation/user-notes-v1-delete

    def __init__(self,
                 games_id):
        self.games_id = games_id
        self.execute()

    def execute(self):
        # verify input data
        assert self.games_id is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='DELETE',
                          endpoint='user/notes/v1',
                          security='oa2',
                          params={},
                          header={},
                          body=self.games_id
                          )


class ITADGetShopsInfo(ITADBaseClass):
    # https://docs.isthereanydeal.com/#tag/Shops/operation/service-shops-v1
    def __init__(self, country_code):
        self.country_code = country_code
        self.execute()

    def execute(self):
        # verify input data
        assert self.country_code is not None, MSG_PARAM_NONE

        # make request
        self.send_request(method='GET',
                          endpoint='service/shops/v1',
                          security='key',
                          params={'country': self.country_code},
                          header={},
                          body={}
                          )

        # process response data
        if self.resp_code == 200:
            self.df = DataFrame(self.resp)
            if not self.df.empty:
                self.shop_id = self.df['id'].to_list()
                self.shop_title = self.df['title'].to_list()
                self.shop_number_of_deals = self.df['deals'].to_list()
                self.shop_number_of_games = self.df['games'].to_list()
                self.upd_date = self.df['update'].to_list()
            else:
                self.shop_id = None
                self.shop_title = None
                self.shop_number_of_deals = None
                self.shop_number_of_games = None
                self.upd_date = None

# ==================== Auxiliary functions ====================


def len_opt_arg(x, n):
    return x is None or len(x) == n


def len_oblig_arg(x, n):
    return len(x) == n


def print_vert(x):
    print(*x, sep='\n')


def print_tit(x):
    print('')
    print_color.print(x, color='blue')


def print_sep():
    print('')
    print_color.print('========================================', color='blue')


def print_err(x):
    print_color.print(x, color='red')


def print_ok(x):
    print_color.print(x, color='green')


# ==================== Main ====================

if __name__ == '__main__':

    """
    Example of use of the ITAD API classes
    """

    # ==================== INITIAL SETTINGS ====================
    print_sep()
    print_tit('Start test')

    pandas.set_option('display.max_colwidth', None)

    ITADBaseClass.get_access_token(api_key=private_data.API_KEY,
                                   client_id=private_data.CLIENT_ID,
                                   client_secret=private_data.CLIENT_SECRET)

    # ==================== EXAMPLE GAMES ====================
    # Tip: use games you don't have in your collection or watlist to avoid modification of yor data
    game_id1 = '018d937f-3a3b-7210-bd2d-0d1dfb1d84c0'  # Red Deat Redemption 2
    game_id2 = '018d937f-5233-732a-9727-ab9b4d72c304'  # Final Fantasy

    debug_parts = {'game_info': True,
                   'waitlist': True,
                   'collection': True,
                   'copies': True,
                   'categories': True,
                   'user': True,
                   'shops': True
                   }

    # ==================== SEARCH GAMES & INFO ====================
    if debug_parts['game_info']:
        print_sep()

        x1 = ITADSearchGames(game_title_to_search='teken 8',
                             max_results=999)
        print_tit(
            f'{x1.found_games_number} games found games for \'{x1.game_title_to_search}\', showing 10:')
        print_vert(x1.found_games_title[0:10])

        x2 = ITADGetGameInfo(game_id=game_id1)
        print_tit(f'Get game info for Game ID: {x2.game_id}')
        print(x2.game_info)

        ids = [game_id1,
               game_id2]
        titles = ITADBaseClass.get_games_title(games_id=ids)
        urls = ITADBaseClass.get_games_url(games_id=ids)
        print_tit('Get titles and URLs for various Game IDs')
        print(DataFrame({'ID': ids, 'titles': titles, 'urls': urls}))

        id = game_id1
        title = ITADBaseClass.get_game_title(game_id=id)
        url = ITADBaseClass.get_game_url(game_id=id)
        print_tit('Get title and URL for one Game ID')
        print(DataFrame({'ID': [id], 'title': [title], 'urls': [url]}))

    # ==================== WAITLIST  ====================
    if debug_parts['waitlist']:
        print_sep()

        x3 = ITADGetGamesFromWaitlist()
        print_tit(f'{x3.waitlist_games_number} games in Wailist, showing 10:')
        print_vert(x3.waitlist_games_title[0:10])

        x4 = ITADPutGamesIntoWaitlist(games_id=[game_id1, game_id2])
        print_tit(f'Added {len(x4.games_id)} games to waitlist:')
        print_vert(x4.games_id)

        x3.execute()
        print_tit(f'{x3.waitlist_games_number} games in Wailist')

        x5 = ITADDeleteGamesFromWaitlist(games_id=[game_id1, game_id2])
        print_tit(f'Removed {len(x5.games_id)} games from waitlist:')
        print_vert(x5.games_id)
        x3.execute()
        print_tit(f'{x3.waitlist_games_number} games in Wailist.')

    # ==================== COLLECTION ====================
    if debug_parts['collection']:
        print_sep()

        x6 = ITADGetGamesFromCollection()
        print_tit(
            f'{x6.collection_games_number} games in collection, showing 10:')
        print_vert(x6.collection_games_title[0:10])

        x7 = ITADPutGamesIntoCollection(games_id=[game_id1, game_id2])
        print_tit(f'Added {len(x7.games_id)} games to collection:')
        print_vert(x7.games_id)
        x6.execute()
        print_tit(f'{x6.collection_games_number} games in collection')

        x8 = ITADDeleteGamesFromCollection(games_id=[game_id1, game_id2])
        print_tit(f'Removed {len(x8.games_id)} games from collection:')
        print_vert(x8.games_id)
        x6.execute()
        print_tit(f'{x6.collection_games_number} games in collection')

    # ==================== COPIES ====================
    if debug_parts['copies']:
        print_sep()

        x9 = ITADGetCopiesOfGames(games_id_to_search=[game_id1, game_id2])
        print_tit('Copies found:')
        print(x9.df)

        x10 = ITADAddCopiesToGames(copies_game_id=[game_id1, game_id2],
                                   copies_redeemed=[True, True],
                                   copies_shop_id=[1, 1],
                                   copies_price_eur=None,
                                   copies_note=None,
                                   copies_tags=None
                                   )
        print_tit('Copies added to games (games also added to colletion):')
        print(DataFrame({'Copies': x10.copies_game_id}))
        x9.execute()
        print_tit('Copies found after addition:')
        print(x9.df)

        x10 = ITADUpdateCopiesFromGames(copies_id=x9.copies_id,
                                        copies_redeemed=[False, False],
                                        copies_shop_id=[3, 3],
                                        copies_price_eur=[5, 6],
                                        copies_note=['note x', 'note 2'],
                                        copies_tags=[['tag1', 'tag2'], ['tag3', 'tag3']])
        print_tit('Copies uptated:')
        print_vert(x10.copies_id)
        x9.execute()
        print_tit('Copies found after update:')
        print(x9.df)

        x11 = ITADDeleteCopies(copies_id=x9.copies_id)
        print_tit('Deleted copies with ID:')
        print_vert(x11.copies_id)
        x9.execute()
        print_tit('Copies found after deletion:')
        print(x9.df)

        x8.execute()
        print_tit(f'Removed {len(x8.games_id)} games from collection:')
        print_vert(x8.games_id)

    # ==================== CATERORIES ====================
    if debug_parts['categories']:
        print_sep()

        x13 = ITADGetCategories()
        print_tit('All categories:')
        print(x13.df)

        x14a = ITADCreateNewCategory(category_title='New cat 1',
                                     category_public=False)
        print_tit('Added a new category 1:')
        print(DataFrame({'ID': [x14a.created_category_id],
                         'Title': [x14a.created_category_title],
                         'Public': [x14a.created_category_public]}))

        x14b = ITADCreateNewCategory(category_title='New cat 2',
                                     category_public=False)
        print_tit('Added a new category 2:')
        print(DataFrame({'ID': [x14b.created_category_id],
                         'Title': [x14b.created_category_title],
                         'Public': [x14b.created_category_public]}))

        print_tit('All categories after additions:')
        x13.execute()
        print(x13.df)

        x15 = ITADUpdateCategories(categories_upd_id=[x14a.created_category_id,
                                                      x14b.created_category_id],
                                   categories_upd_title=['Updated cat 1',
                                                         'Updated cat 2'],
                                   categories_upd_public=[False,
                                                          False],
                                   categories_upd_position=[91,
                                                            92])
        print_tit('Updated categories:')
        print(DataFrame({'ID': x15.categories_upd_id,
                         'Title': x15.categories_upd_title,
                         'Public': x15.categories_upd_public,
                         'Position': x15.categories_upd_position}))
        print_tit('All categories afte update (response):')
        print(x15.df)

        x16 = ITADDeleteCategories([x14a.created_category_id,
                                    x14b.created_category_id])
        print_tit('Deleted categories:')
        print_vert(x16.categories_del_id)
        print_tit('All categories after deletion:')
        x13.execute()
        print(x13.df)

    # ==================== USER ====================
    if debug_parts['user']:
        print_sep()

        x17 = ITADGetUserInfo()
        print_tit('Get user name:')
        print(x17.username)

        x18 = ITADGetUserNotes()
        print_tit('Get user notes, showing 0-10:')
        print(x18.df[0:10])

        x19 = ITADPutUserNotesToGame(games_id=[game_id1, game_id2],
                                     games_note=['bb', 'cc'])
        print_tit('Add user notes to game:')
        print(DataFrame({'Game ID': x19.games_id,
                         'Title': ITADBaseClass.get_games_title(x19.games_id),
                         'Note': x19.games_note}
                        ))

        x20 = ITADDeleteUserNotesFromGame([game_id1, game_id2])
        print_tit('Delete user notes from games:')
        print(DataFrame({'Game ID': x20.games_id,
                         'Game Title': ITADBaseClass.get_games_title(x20.games_id)
                         }))

    # ==================== SHOPS ====================
    if debug_parts['shops']:
        print_sep()

        x21 = ITADGetShopsInfo('ES')
        print_tit('Get all shops:')
        print(x21.df)

    print_sep()
    print_tit('Done')
