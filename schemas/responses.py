from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class AuthorModel(BaseModel):
    id: int
    name: str


class LikeModel(BaseModel):
    user_id: int
    name: str


class TweetModel(BaseModel):
    id: int
    content: str
    attachments: Optional[List[str]] = []
    author: AuthorModel
    likes: List[LikeModel]


class TweetsResponseModel(BaseModel):
    result: bool
    tweets: List[TweetModel]


class TweetResponseModel(BaseModel):
    result: bool
    tweet_id: int


class UserModel(BaseModel):
    id: int
    name: str


class UserProfile(BaseModel):
    id: int
    name: str
    followers: List[UserModel]
    following: List[UserModel]


class UserResponseModel(BaseModel):
    result: bool
    user: Optional[UserProfile] = None


class MediaResponseModel(BaseModel):
    result: bool
    media_id: int
