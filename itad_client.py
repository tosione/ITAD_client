# itad_client.py
# IsThereAnyDeal (ITAD) API client using OAuth2
#
# Author: Tosione
# Date: 2026-01-03

import requests_oauthlib
import webbrowser
import json
import os
import datetime
from print_color import print as printc
import private_data


# https://docs.isthereanydeal.com/
# https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html


# Application data
API_KEY = private_data.API_KEY
CLIENT_ID = private_data.CLIENT_ID
CLIENT_SECRET = private_data.CLIENT_SECRET
REDIRECT_URI = "https://localhost"
SCOPE = ["user_info", "notes_read", "notes_write", "profiles",
         "wait_read", "wait_write", "coll_read", "coll_write"]
AUTH_URL = "https://isthereanydeal.com/oauth/authorize/"
TOKEN_URL = "https://isthereanydeal.com/oauth/token/"
BASE_URL = "https://api.isthereanydeal.com/"
TOKEN_FILE = "itad_tokens.json"


def get_tokens(OASes):
    if os.path.exists(TOKEN_FILE):
        load_tokens_from_file(OASes)
        refresh_tokens_at_ITAD(OASes)
        save_tokens_to_file(OASes)
    else:
        obtain_new_tokens_from_ITAD(OASes)
        save_tokens_to_file(OASes)


def load_tokens_from_file(OASes):
    try:
        with open(TOKEN_FILE, "r") as f:
            OASes.token = json.load(f)
    except Exception as e:
        print("Error loading tokens:", e)
        OASes.token = None


def save_tokens_to_file(OAses):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(OAses.token, f, indent=4)
    except Exception as e:
        print("Error saving tokens:", e)


def obtain_new_tokens_from_ITAD(OASes):
    # Step 1: obtain authorization URL
    authorization_url, state = OASes.authorization_url(AUTH_URL)

    # Step 2: open URL in browser, ask user to authorize and copy the redirect URL
    print("Please go to this URL and authorize access:")
    print(authorization_url)
    webbrowser.open(authorization_url)

    # Step 3: Get the authorization verifier code from the callback url
    redirect_URL = input("\nPaste the full redirect URL here: ")

    # Step 4: Fetch the access token
    OASes.fetch_token(TOKEN_URL, authorization_response=redirect_URL)

    print(f"Tokens expires in {OASes.token['expires_in']/3600/24} days.")
    print(
        f"Tokens expires at {datetime.datetime.fromtimestamp(OASes.token['expires_at'])}.")


def refresh_tokens_at_ITAD(OASes):
    OASes.refresh_token(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET))


def is_OAuth_ok(OASes):
    # Check if OAuth is OK by making a test request
    return OASes.get(BASE_URL + "user/info/v2").status_code == 200


def get_data(OASes, endpoint):
    # Get data from endpoint
    return OASes.get(BASE_URL + endpoint).content


def get_data_text(OASes, endpoint):
    # Get data from endpoint as text
    return OASes.get(BASE_URL + endpoint).text


if __name__ == "__main__":
    # Clear console on Windows
    if os.name == 'nt':
        os.system('cls')

    # Create an OAuth2 Session
    OASes = requests_oauthlib.OAuth2Session(client_id=CLIENT_ID,
                                            redirect_uri=REDIRECT_URI,
                                            scope=SCOPE,
                                            pkce="S256")

    # Get tokens
    get_tokens(OASes)

    if is_OAuth_ok(OASes):
        printc("OAuth is working", color='green')
    else:
        printc("OAuth is not working", color='red')

    data = get_data(OASes, "user/info/v2")
    printc(data, color='purple')
