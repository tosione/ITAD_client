# Description

IsThereAnyDeal (ITAD) API client using Python and OAuth2 authentication for personal data, or API key authentication for non-personal data.

Main functions:
- **get_oauth_access_token**: handles all the token obtention for OAuth2. Browser will be launched to get authorization through ITAD. The redirected URL must be copied to the terminal to obtain tokens for script. This will only happen once, as the tokens will be saved to JSON file, and tokens will be refreshed eacht time they are used.
- **send_request**: sends data request, handling authorizations (wheter its with OAuth2 or API Key).
