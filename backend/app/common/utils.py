from enum import Enum


class Role(str, Enum):
    admin = "admin"
    user = "user"


class PostType(str, Enum):
    link = "link"
    pdf = "pdf"
