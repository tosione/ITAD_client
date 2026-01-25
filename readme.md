# Description
[IsThereAnyDeal](https://isthereanydeal.com) (ITAD) API client using Python and OAuth2 authentication for personal data, or API key authentication for non-personal data.

This module provides a client for interacting with the IsThereAnyDeal
(ITAD) API. It supports OAuth2 authentication for personal data and API
key authentication for non-personal data.

The client allows you to perform various operations such as retrieving
user information, searching for games, managing collections, managing
waitlists, and more. It provides high-level functions for making API
requests and handling authentication.

This module uses the `requests_oauthlib` library for OAuth2 authentication
and the `print_color` library for colored printing.

For privacy reasons, the API_KEY, CLIENT_ID, and CLIENT_SECRET are
stored in the `private_data.py` module. User must generate its own
`private_data.py` were this constants must be defined.

For more information on the ITAD API, refer to the official
 IsThereAnyDeal [Documentation](https://docs.isthereanydeal.com/) or [GITHub](https://github.com/IsThereAnyDeal/API).

For mor information on OAuth2:
- [Requests-OAuthlib: OAuth 2 Workflow](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html)
- [Proof Key of Code Exchange (PKCE)](https://docs.secureauth.com/ciam/en/proof-key-of-code-exchange--pkce-.html)
- [OAuth 2.0 Explained With Simple Terms](https://bytebytego.com/guides/oauth-2-explained-with-siple-terms/)

Author: [tosione](https://https://github.com/tosione)

# Classes

- `BaseClass`: Base class for all ITAD client classes.
    - `get_access_token`: loads from JSON or obtains new tokens.
    - `get_new_tokens_from_itad`: obtains new tokens.
    - `test_oauth_session`: tests the OAuth2 session.
    - `send_request`: sends data a request to ITAD.
    - `get_games_title`: retrieves the titles of multiple games.
    - `get_game_title`: retrieves the title of a single game.
    - `get_game_url`: gets the URL of a game.
    - `get_games_url`: gets the URLs of multiple games.
    - `save_json`: Saves JSON data to a file.
    - `load_json`: Loads JSON data from a file.
- `SearchGames`
- `GetGameInfo`
- `GetGamesFromWaitlist`
- `PutGamesIntoWaitlist`
- `DeleteGamesFromWaitlist`
- `GetGamesFromCollection`
- `PutGamesIntoCollection`
- `DelGamesFromCollection`
- `GetCopiesOfGames`
- `AddCopiesToGames`
- `UpdateCopiesOfGames`
- `DeleteCopiesOfGames`
- `GetCategories`
- `CreateNewCategory`
- `UpdateCategories`
- `DeleteCategories`
- `GetUserInfo`
- `GetUserNotes`
- `PutUserNotesFromGame`
- `DeleteUserNotesFromGame`
- `GetShopsInfo`
