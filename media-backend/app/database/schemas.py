import datetime as _dt
import pydantic as _pydantic

class _BaseModel(_pydantic.BaseModel):
     class Config:
        orm_mode = True
        from_attributes = True

class _BaseMedia(_BaseModel):
    title: str
    artist_id: int
    time: _dt.datetime
    album_id: int
    users_id: int
    length: int
    genre: str = None

class Media (_BaseMedia):
    id: int
    time: str
    length: str
    artist_name: str
    album_name: str

class CreateMedia(_BaseMedia):
    pass

class _BaseArtist(_BaseModel):
    name: str

class Artist (_BaseArtist):
    id: int

class CreateArtist(_BaseArtist):
    pass

class _BaseAlbum(_BaseModel):
    name: str

class Album (_BaseAlbum):
    id: int

class CreateAlbum(_BaseAlbum):
    pass

class _UserBase(_BaseModel):
    email: str

class User (_UserBase):
    id: int
    date_created: _dt.datetime

class UserCreate(_UserBase):
    password: str

class _PostBase(_BaseModel):
    post_text: str

class PostCreate(_PostBase):
    pass

class Post(_PostBase):
    id: int
    owner_id: int
    date_created: _dt.datetime