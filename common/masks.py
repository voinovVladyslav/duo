import re

from pydantic import EmailStr, validate_email
from pydantic_core import PydanticCustomError

# all letters and numbers except first
WORD_REGEX = re.compile(r'(?<=^\w)[\w\W]+(?=@)')


def mask_email(email: EmailStr) -> str:
    """
    replaces all email characters with * except first and after @
    `test@example.com` -> `t***@example.com`
    if not valid email, then no mask
    """
    try:
        start, email = validate_email(email)
    except PydanticCustomError:
        return email
    replace_with = f'{start[0]}{len(start[1:]) * "*"}'
    return email.replace(start, replace_with, 1)
