"""Read the authenticated C411 profile."""


from aiohttp import ClientError, ClientSession, ClientTimeout

URL = "https://c411.org/api/user/profile"


class ProfileError(Exception):
    """The profile could not be retrieved."""


class InvalidKey(ProfileError):
    """The API key was rejected."""


class MissingScope(InvalidKey):
    """The key lacks profile:read."""


async def fetch_profile(session: ClientSession, key: str) -> dict:
    """Retrieve the profile without following redirects."""
    try:
        async with session.get(
            URL,
            headers={"Authorization": f"Bearer {key}"},
            allow_redirects=False,
            timeout=ClientTimeout(total=15),
        ) as response:
            if response.status == 401:
                raise InvalidKey("C411 rejected the API key")
            if response.status == 403:
                raise MissingScope("C411 requires profile:read")
            if response.status != 200:
                raise ProfileError(f"C411 returned HTTP {response.status}")
            profile = await response.json()
    except (ClientError, TimeoutError, ValueError):
        raise ProfileError("Could not read the C411 profile") from None

    if (
        not isinstance(profile, dict)
        or type(profile.get("id")) is not int
        or not isinstance(profile.get("username"), str)
        or not profile["username"].strip()
    ):
        raise ProfileError("C411 returned an invalid profile")
    return profile
