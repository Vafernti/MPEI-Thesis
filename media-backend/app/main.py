import os
from typing import TYPE_CHECKING, List
from fastapi.responses import FileResponse
import logging
import fastapi as _fastapi
import sqlalchemy.orm as _orm
import fastapi.security as _security
import datetime as _dt
import threading
import time
from mutagen.mp4 import MP4
from app.database import schemas as _schemas
from app.database import services as _services
from app.database import models as _models, database as _database

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

app = _fastapi.FastAPI()

# Base directory for users uploads
UPLOAD_DIR = "users_media"

# Ensure the base upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

#Helper function to het the user's upload directory
def get_user_upload_dir(user_id: int) -> str:
    user_dir = os.path.join(UPLOAD_DIR, f"id_{user_id}_media")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def reformat_datetime(dt: _dt.datetime) -> str:
    """Reformat a datetime object to 'YYYY-MM-DD, HH:MM:SS' format."""
    formatted_date = dt.strftime("%Y-%m-%d, %H:%M:%S")
    return formatted_date

def format_length(seconds: int) -> str:
    """Convert seconds into MM:SS format."""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}"

@app.get("/api")
async def root():
    return {"message": "MyMedia"}

@app.post("/api/upload/")
async def upload_file(
    file: _fastapi.UploadFile = _fastapi.File(...),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    user_dir = get_user_upload_dir(user.id)
    print(f"User directory: {user_dir}")  # Debugging print statement
    file_path = os.path.join(user_dir, file.filename)

    # Check if the file already exists to prevent overwriting
    if os.path.exists(file_path):
        raise _fastapi.HTTPException(status_code=400, detail="File already exists")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract metadata using mutagen for m4a files
    try:
        audio = MP4(file_path)
        filename = file.filename
        artist_name = audio.tags.get('\xa9ART', ["Unknown Artist"])[0]  # Get artist name
        album_name = audio.tags.get('\xa9alb', ["Unknown Album"])[0]    # Get album name
        length = int(audio.info.length)  # Get track length
        genre = audio.tags.get('\xa9gen', ["Unknown Genre"])[0]  # Get genre
    except Exception as e:
        artist_name = "Unknown Artist"
        album_name = "Unknown Album"
        length = 0
        genre = "Unknown Genre"

    # Get or create artist and album
    artist = await _services.get_or_create_artist(artist_name=artist_name, db=db)
    album = await _services.get_or_create_album(album_name=album_name, db=db)

    # Save metadata to the database
    media_data = _schemas.CreateMedia(
        title=filename,
        artist_id=artist.id,
        time=_dt.datetime.utcnow(),
        album_id=album.id,
        users_id=user.id,
        length=length,
        genre=genre
    )
    await _services.create_media(media=media_data, db=db)

    return {"filename": file.filename, "path": file_path}


@app.get("/api/download/{filename}", response_class=FileResponse)
async def download_file(
    filename: str,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    user_dir = get_user_upload_dir(user.id)
    file_path = os.path.join(user_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type="application/octet-stream", filename=filename)
    else:
        raise _fastapi.HTTPException(status_code=404, detail="File not found")
    
@app.delete("/api/delete/{filename}")
async def delete_file(
    filename: str,
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    user_dir = get_user_upload_dir(user.id)
    file_path = os.path.join(user_dir, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)

        # Remove the corresponding database entry
        media = db.query(_models.Media).filter(
            _models.Media.users_id == user.id,
            _models.Media.title == filename
        ).first()
        if media:
            db.delete(media)
            db.commit()
        return {"detail": "File successfully deleted"}
    else:
        raise _fastapi.HTTPException(status_code=404, detail="File not found")

def cleanup_orphaned_entries():
    while True:
        db = _database.SessionLocal()
        try:
            media_files = db.query(_models.Media).all()
            for media in media_files:
                user_dir = get_user_upload_dir(media.users_id)
                file_path = os.path.join(user_dir, media.title)
                if not os.path.exists(file_path):
                    db.delete(media)
                    db.commit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            db.close()
        # Run cleanup every hour (3600 seconds)
        time.sleep(10)

# Start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_orphaned_entries, daemon=True)
cleanup_thread.start()

@app.post("/api/media", response_model=_schemas.Media)
async def create_media(
    media: _schemas.CreateMedia, 
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    return await _services.create_media(media=media, db=db)

@app.post("/api/artist", response_model=_schemas.Artist)
async def create_artist(
    artist: _schemas.CreateArtist, 
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    return await _services.create_artist(artist=artist, db=db)

@app.post("/api/album", response_model=_schemas.Album)
async def create_album(
    album: _schemas.CreateAlbum, 
    user: _schemas.User = _fastapi.Depends(_services.get_current_user),
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    return await _services.create_album(album=album, db=db)

@app.post("/api/users")
async def create_user(
    user: _schemas.UserCreate, 
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    db_user = await _services.get_user_by_email(email=user.email, db=db)
    if db_user:
        raise _fastapi.HTTPException(
            status_code=400, detail="User with that email already exists"
        )
#create the user
    user = await _services.create_user(user=user, db=db)
#return the JWT token
    return await _services.create_token(user=user)


@app.post("/api/token")
async def generate_token(
    form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(),
    db: "_orm.Session" = _fastapi.Depends(_services.get_db),
):
    user = await _services.authenticate_user(
        email=form_data.username, password=form_data.password, db=db
    )
    
    if not user: 
        raise _fastapi.HTTPException(status_code=401, detail="Invalid credentials")
    
    return await _services.create_token(user=user)

@app.get("/api/users/me", response_model=_schemas.User)
async def get_user(user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    return user

@app.post("/api/posts", response_model=_schemas.Post)
async def create_post(
    post: _schemas.PostCreate, 
    user: _schemas.User = _fastapi.Depends(_services.get_current_user), 
    db: "_orm.Session" = _fastapi.Depends(_services.get_db)
):
    return await _services.create_post(user=user, db=db, post=post)

@app.get("/api/posts", response_model=List[_schemas.Post])
async def get_user_posts(
    user: _schemas.User = _fastapi.Depends(_services.get_current_user), 
    db: _orm.Session = _fastapi.Depends(_services.get_db)
): 
    return await _services._get_user_posts(user=user, db=db)

@app.get("/api/media/", response_model=list[_schemas.Media])
async def list_media(
    db: _orm.Session = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    media_files = db.query(_models.Media).options(
        _orm.joinedload(_models.Media.artist),
        _orm.joinedload(_models.Media.album)
    ).filter(_models.Media.users_id == user.id).all()

    valid_media_files = []

    for media in media_files:
        user_dir = get_user_upload_dir(user.id)
        file_path = os.path.join(user_dir, media.title)
        if os.path.exists(file_path):
            valid_media_files.append({
                "id": media.id,
                "title": media.title,
                "artist_id": media.artist.id,
                "artist_name": media.artist.name,
                "album_id": media.album.id,
                "album_name": media.album.name,
                "time": reformat_datetime(media.time),
                "users_id": media.users_id,
                "length": format_length(media.length),
                "genre": media.genre
            })
        else:
            db.delete(media)
            db.commit()

    return valid_media_files

@app.get("/api/media/{id}/", response_model=_schemas.Media)
async def get_media(
    id: int, 
    db: "_orm.Session" = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    media = await _services.get_media(id=id, db=db)
    if media is None:
        raise _fastapi.HTTPException(status_code=404, detail="Mediafile does not exist")
    return media

@app.get("/api/album/{id}/", response_model=_schemas.Album)
async def get_album(
    id: int,
    db: "_orm.Session" = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    album = await _services.get_album(id=id, db=db)
    if album is None:
        raise _fastapi.HTTPException(status_code=404, detail="Album does not exist")
    return album

@app.get("/api/artist/{id}/", response_model=_schemas.Artist)
async def get_artist(
    id: int, 
    db: "_orm.Session" = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    artist = await _services.get_artist(id=id, db=db)
    if artist is None:
        raise _fastapi.HTTPException(status_code=404, detail="Artist does not exist")
    return artist
   
@app.delete("/api/media/{id}/")
async def delete_media(
    id: int,
    db: "_orm.Session"= _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    media = await _services.get_media(db=db, id=id)
    if media is None:
        raise _fastapi.HTTPException(status_code=404, detail="Mediafile does not exist")
    
    await _services.delete_media(media, db=db)
    return "Media was deleted successfully"


@app.put("/api/media/{id}/", response_model=_schemas.Media)
async def update_media(
    id: int, 
    media_data:_schemas.CreateMedia, 
    db: "_orm.Session" = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    media = await _services.get_media(id=id, db=db)
    if media is None:
        raise _fastapi.HTTPException(status_code=404, detail="Mediafile does not exist")
    
    return await _services.update_media(
        media_data=media_data, media=media, db=db
    )