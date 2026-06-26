from ninja import Schema
from typing import Optional


class LoginIn(Schema):
    username: str
    password: str


class RegisterIn(Schema):
    username: str
    password: str
    email: str = ''
    role: str = 'designer'


class RefreshIn(Schema):
    refresh_token: str


class TokenOut(Schema):
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'


class UserOut(Schema):
    id: int
    username: str
    email: str
    role: str
    avatar: str = ''
    is_admin: bool = False


class ErrorOut(Schema):
    code: str
    message: str
