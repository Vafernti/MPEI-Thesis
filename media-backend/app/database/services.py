from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException
import fastapi as _fastapi
import fastapi.security as _security
import email_validator as _email_check
import passlib.hash as _hash
import jwt as _jwt
oauth2schema = _security.OAuth2PasswordBearer("/api/token")
import pydantic as _pydantic
import app.database.database as _database
import app.database.models as _models      
import app.database.schemas as _schemas
import os


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_JWT_SECRET = os.getenv("JWT_SECRET", "thisisnotverysafe")

def _add_tables():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try: 
        yield db
    finally:
        db.close()

async def create_instance(model_instance: _pydantic.BaseModel, db: "Session") -> _pydantic.BaseModel:
    db.add(model_instance)
    db.commit()
    db.refresh(model_instance)
    return model_instance

async def create_media(media: _schemas.CreateMedia, db: "Session") -> _schemas.Media:
    media_instance = _models.Media(**media.dict())
    return await create_instance(media_instance, db)

async def create_artist(artist: _schemas.CreateArtist, db: "Session") -> _schemas.Artist:
    artist_instance = _models.Artist(**artist.dict())
    return await create_instance(artist_instance, db)

async def create_album(album: _schemas.CreateAlbum, db: "Session") -> _schemas.Album:
    album_instance = _models.Album(**album.dict())
    return await create_instance(album_instance, db)

async def get_all_media(db: "Session") -> list[_schemas.Media]:
    media_instance = db.query(_models.Media).all()
    return list (map(_schemas.Media.from_orm, media_instance))

async def get_media(id: int, db: "Session"):
    return db.query(_models.Media).filter(_models.Media.id == id).first()

async def get_album(id: int, db: "Session"):
    return db.query(_models.Album).filter(_models.Album.id == id).first()

async def get_artist(id: int, db: "Session"):
    return db.query(_models.Artist).filter(_models.Artist.id == id).first()

async def delete_media(media: _models.Media, db: "Session"):
    db.delete(media)
    db.commit()

async def update_media(
    media_data: _schemas.CreateMedia, 
    media: _models.Media, 
    db: "Session"
) -> _schemas.Media:
    media.title = media_data.title

    db.commit()
    db.refresh(media)

    return _schemas.Media.from_orm(media)

async def get_user_by_email(
    email: str,
    db: "Session"
):
    return db.query(_models.User).filter(_models.User.email == email).first()

async def create_user(
    user: _schemas.UserCreate, 
    db: "Session"
):
# check that email is valid
    try: 
        # Validate email
        valid = _email_check.validate_email(user.email)
        email = valid.email
    except _email_check.EmailNotValidError:
        raise _fastapi.HTTPException(
            status_code=404, detail= "Please enter a valid email"
        )
    hashed_password = _hash.bcrypt.hash(user.password)
    user_obj = _models.User(email=email, hashed_password=hashed_password)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj
    
async def create_token(user: _models.User):
    user_schema_obj = _schemas.User.from_orm(user)
    user_dict = user_schema_obj.dict()
    del user_dict["date_created"]
    token = _jwt.encode(user_dict, _JWT_SECRET, algorithm="HS256")
    return dict(access_token=token, token_type="bearer")

async def authenticate_user(email: str, password: str, db: "Session"):
    user = await get_user_by_email(email=email, db=db)
    if not user or not user.verify_password(password=password):
        return False
    return user

async def get_current_user(
    db: "Session"=_fastapi.Depends(get_db), 
    token: str=_fastapi.Depends(oauth2schema),
):
    try: 
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid email or password"
        )
    return _schemas.User.from_orm(user)

async def create_post(user: _schemas.User, db: "Session", post: _schemas.PostCreate):
    post = _models.Post(**post.dict(), owner_id=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _schemas.Post.from_orm(post)

async def _get_user_posts(user: _schemas.User, db: "Session"):
    posts = db.query(_models.Post).filter_by(owner_id=user.id)
    return list(map(_schemas.Post.from_orm, posts))

async def get_or_create_entity(entity_class, name: str, db: "Session"):
    entity = db.query(entity_class).filter(entity_class.name == name).first()
    if entity is None:
        entity = entity_class(name=name)
        db.add(entity)
        db.commit()
        db.refresh(entity)
    return entity

async def get_or_create_artist(artist_name: str, db: "Session") -> _models.Artist:
    return await get_or_create_entity(_models.Artist, artist_name, db)

async def get_or_create_album(album_name: str, db: "Session") -> _models.Album:
    return await get_or_create_entity(_models.Album, album_name, db)