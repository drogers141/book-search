import unicodedata
import re
import random


MAX_SUFFIX_LEN = 7
ALPHA_NUM_LOWER = '01234567989abcdefghijklmnopqrstuvwxyz'
MIN_USER_NAME_LEN = 3


def generate_base_username(email: str, substitute: str='user') -> str:
    username = unicodedata.normalize('NFKD', email)
    username = username.encode("ascii", "ignore").decode("ascii")
    username = username.split('@')[0]
    username = substitute if not username else username
    username = re.sub(r"[^\w\s.-]", "", username)
    username = re.sub(r"\s+", "_", username).lower()
    if len(username) < MIN_USER_NAME_LEN:
        username = substitute
    return username


def generate_candidate_usernames(username: str) -> [str]:
    retlist = [username,]
    for i in range(MAX_SUFFIX_LEN):
        suffix = ''
        for j in range(i+1):
            suffix += random.choice(ALPHA_NUM_LOWER)
        retlist.append(username + suffix)
    return retlist


def generate_unique_username(email: str, substitute: str='user') -> str:
    """Generate a username from an email address that is unique in this db.

    We don't care about the username as login is email only, they just need
    to be unique.

    This algorithm is similar the same as django-allauth uses under the
    hood, but I didn't want to rely on their internals.  It is better tested,
    though.

    :param email - valid email address
    :param substitute - substitute base username if the local part of the email
        reduced to ascii is whitespace
    """
    from .models import BookSearchUser

    base_username = generate_base_username(email, substitute)
    candidates = generate_candidate_usernames(base_username)
    existing_users = set([user.username.lower() for user in BookSearchUser.objects.all()])
    for candidate in candidates:
        if candidate not in existing_users:
            return candidate
    return NotImplementedError('Could not generate unique username')
