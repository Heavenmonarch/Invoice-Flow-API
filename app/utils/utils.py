import re


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def fullname(firstname: str, lastname: str) -> str:
    return firstname + " " + lastname