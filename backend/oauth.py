"""
OAuth Social Login Module for NarrAI.
Supports Google, Facebook, and X (Twitter) OAuth 2.0 flows.
Each provider requires CLIENT_ID and CLIENT_SECRET in environment variables.
Gracefully handles missing authlib if running in a minimal environment.
"""
import os

try:
    from authlib.integrations.starlette_client import OAuth
    oauth = OAuth()
    AUTHLIB_AVAILABLE = True
except ImportError:
    oauth = None
    AUTHLIB_AVAILABLE = False

# ====================== GOOGLE ======================
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

if AUTHLIB_AVAILABLE and GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

# ====================== FACEBOOK ======================
FACEBOOK_CLIENT_ID = os.environ.get("FACEBOOK_CLIENT_ID", "")
FACEBOOK_CLIENT_SECRET = os.environ.get("FACEBOOK_CLIENT_SECRET", "")

if AUTHLIB_AVAILABLE and FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET:
    oauth.register(
        name='facebook',
        client_id=FACEBOOK_CLIENT_ID,
        client_secret=FACEBOOK_CLIENT_SECRET,
        access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
        authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
        api_base_url='https://graph.facebook.com/v18.0/',
        client_kwargs={'scope': 'email public_profile'},
    )

# ====================== X (TWITTER) ======================
X_CLIENT_ID = os.environ.get("X_CLIENT_ID", "")
X_CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET", "")

if AUTHLIB_AVAILABLE and X_CLIENT_ID and X_CLIENT_SECRET:
    oauth.register(
        name='x',
        client_id=X_CLIENT_ID,
        client_secret=X_CLIENT_SECRET,
        access_token_url='https://api.x.com/2/oauth2/token',
        authorize_url='https://x.com/i/oauth2/authorize',
        api_base_url='https://api.x.com/2/',
        client_kwargs={
            'scope': 'tweet.read users.read offline.access',
            'code_challenge_method': 'S256',
        },
    )


def get_available_providers() -> list[str]:
    """Return list of configured OAuth provider names."""
    if not AUTHLIB_AVAILABLE:
        return []
    providers = []
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        providers.append("google")
    if FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET:
        providers.append("facebook")
    if X_CLIENT_ID and X_CLIENT_SECRET:
        providers.append("x")
    return providers


def is_provider_configured(provider: str) -> bool:
    """Check if a given provider has credentials configured."""
    return AUTHLIB_AVAILABLE and (provider in get_available_providers())


async def get_oauth_user_info(provider: str, token: dict) -> dict | None:
    """
    Fetch user profile from OAuth provider after successful authentication.
    Returns dict with: email, name, avatar_url, provider_account_id
    """
    if not AUTHLIB_AVAILABLE or not oauth:
        return None
    try:
        if provider == "google":
            userinfo = token.get("userinfo", {})
            return {
                "email": userinfo.get("email"),
                "name": userinfo.get("name"),
                "avatar_url": userinfo.get("picture"),
                "provider_account_id": userinfo.get("sub"),
            }

        elif provider == "facebook":
            client = oauth.create_client("facebook")
            resp = await client.get(
                'me?fields=id,name,email,picture.type(large)',
                token=token,
            )
            profile = resp.json()
            return {
                "email": profile.get("email"),
                "name": profile.get("name"),
                "avatar_url": profile.get("picture", {}).get("data", {}).get("url"),
                "provider_account_id": profile.get("id"),
            }

        elif provider == "x":
            client = oauth.create_client("x")
            resp = await client.get(
                'users/me?user.fields=id,name,username,profile_image_url',
                token=token,
            )
            data = resp.json().get("data", {})
            return {
                "email": None,
                "name": data.get("name"),
                "avatar_url": data.get("profile_image_url"),
                "provider_account_id": data.get("id"),
            }

    except Exception as e:
        print(f"OAuth user info error ({provider}): {e}")
        return None
