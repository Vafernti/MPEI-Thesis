import os
import re
from typing import TYPE_CHECKING, List
from fastapi.responses import FileResponse, StreamingResponse
import fastapi as _fastapi
import sqlalchemy.orm as _orm
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
import fastapi.security as _security
import datetime as _dt
import threading
import time
import mutagen
from mutagen.mp4 import MP4
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wavpack import WavPack
from mutagen.aac import AAC
from app.database import schemas as _schemas
from app.database import services as _services
from app.database import models as _models, database as _database
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

app = _fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directory for users uploads
UPLOAD_DIR = "users_media"

# Ensure the base upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


app.mount("/static_files", StaticFiles(directory="static_files"), name="static_files")
app.mount("/users_media", StaticFiles(directory="users_media"), name="users_media")

@app.on_event("startup")
def on_startup():
   _database.init_db()


#Helper function to het the user's upload directory
def get_user_upload_dir(user_id: int) -> str:
    user_dir = os.path.join(UPLOAD_DIR, f"id_{user_id}_media")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def reformat_datetime(dt: _dt) -> str:
    """Reformat a datetime object to 'YYYY-MM-DDTHH:MM:SSZ' format."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

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
    file_path = os.path.join(user_dir, file.filename)

    # Check if the file already exists to prevent overwriting
    if os.path.exists(file_path):
        raise _fastapi.HTTPException(status_code=400, detail="File already exists")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    print(f"File saved to {file_path}")

    # Extract metadata using mutagen for supported audio files
    supported_extensions = [".m4a", ".mp3", ".wav", ".flac", ".aac"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in supported_extensions:
        raise _fastapi.HTTPException(status_code=400, detail="Unsupported file type")

    try:
        audio = None
        cover_image = None
        if file_extension == ".m4a":
            audio = MP4(file_path)
            if 'covr' in audio:
                cover_image = os.path.join(user_dir, f"{os.path.splitext(file.filename)[0]}_cover.jpg")
                with open(cover_image, "wb") as img_file:
                    img_file.write(audio['covr'][0])
                print(f"Extracted cover image for .m4a: {cover_image}")
        elif file_extension == ".mp3":
            audio = MP3(file_path)
            for tag in audio.tags.keys():
                if tag.startswith('APIC:'):
                    cover_image = os.path.join(user_dir, f"{os.path.splitext(file.filename)[0]}_cover.jpg")
                    with open(cover_image, "wb") as img_file:
                        img_file.write(audio.tags[tag].data)
                    print(f"Extracted cover image for .mp3: {cover_image}")
                    break
            artist_name = audio.get('TPE1', ["Unknown Artist"])[0]  # Artist
            album_name = audio.get('TALB', ["Unknown Album"])[0]   # Album
            genre = audio.get('TCON', ["Unknown Genre"])[0]        # Genre
        elif file_extension == ".wav":
            audio = WavPack(file_path)
            # WAV files typically don't contain embedded cover art
        elif file_extension == ".flac":
            audio = FLAC(file_path)
            if audio.pictures:
                cover_image = os.path.join(user_dir, f"{os.path.splitext(file.filename)[0]}_cover.jpg")
                with open(cover_image, "wb") as img_file:
                    img_file.write(audio.pictures[0].data)
                print(f"Extracted cover image for .flac: {cover_image}")
        elif file_extension == ".aac":
            audio = AAC(file_path)
            # Handle AAC cover art if available

        filename = file.filename
        if file_extension != ".mp3":  # already handled above
            artist_name = audio.tags.get('\xa9ART', ["Unknown Artist"])[0] if '\xa9ART' in audio.tags else "Unknown Artist"
            album_name = audio.tags.get('\xa9alb', ["Unknown Album"])[0] if '\xa9alb' in audio.tags else "Unknown Album"
            genre = audio.tags.get('\xa9gen', ["Unknown Genre"])[0] if '\xa9gen' in audio.tags else "Unknown Genre"
        length = int(audio.info.length) if hasattr(audio.info, 'length') else 0

        # Print statements to debug metadata extraction
        print(f"Artist Name: {artist_name}")
        print(f"Album Name: {album_name}")
        print(f"Length: {length}")
        print(f"Genre: {genre}")
        
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        artist_name = "Unknown Artist"
        album_name = "Unknown Album"
        length = 0
        genre = "Unknown Genre"
        cover_image = None

    # Set default cover image if no cover is found
    if not cover_image:
        cover_image = "static_files/default_cover.png"  # Path to the default cover image
        print("No cover image found, using default cover image")

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
        genre=genre,
        cover_image=cover_image
    )
    await _services.create_media(media=media_data, db=db)
    print(f"Saved media data: {media_data}")

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
        print(f"Deleted media file: {file_path}")

        # Remove the corresponding database entry
        media = db.query(_models.Media).filter(
            _models.Media.users_id == user.id,
            _models.Media.title == filename
        ).first()
        if media:
            # Delete the cover image file if it exists
            cover_image_path = media.cover_image
            if cover_image_path and os.path.exists(cover_image_path):
                os.remove(cover_image_path)
                print(f"Deleted cover image file: {cover_image_path}")

            db.delete(media)
            db.commit()
        return {"detail": "File and cover image successfully deleted"}
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
                "genre": media.genre,
                "cover_image": media.cover_image or "static_files/default_cover.png",  # Ensure the cover_image is included
                "path": f"/users_media/id_{media.users_id}_media/{media.title}"  # Ensure the path is correct
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


@app.get("/api/media/search", response_model=list[_schemas.Media])
async def search_media(
    query: str,
    db: _orm.Session = _fastapi.Depends(_services.get_db),
    user: _schemas.User = _fastapi.Depends(_services.get_current_user)
):
    media_files = db.query(_models.Media).join(_models.Artist).join(_models.Album).options(
        joinedload(_models.Media.artist),
        joinedload(_models.Media.album)
    ).filter(
        _models.Media.users_id == user.id,
        or_(
            _models.Media.title.ilike(f"%{query}%"),
            _models.Artist.name.ilike(f"%{query}%"),
            _models.Album.name.ilike(f"%{query}%")
        )
    ).all()

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
                "time": reformat_datetime(media.time),  # Ensure correct format
                "users_id": media.users_id,
                "length": format_length(media.length),
                "genre": media.genre,
                "cover_image": media.cover_image or "static_files/default_cover.png",  # Ensure the cover_image is included
                "path": f"/users_media/id_{media.users_id}_media/{media.title}"  # Ensure the path is correct
            })
        else:
            db.delete(media)
            db.commit()

    return valid_media_files

@app.get("/api/stream/{filename}")
async def stream_file(
    filename: str,
    token: str,
    request: _fastapi.Request,
    db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    try:
        user = await _services.get_current_user(token=token, db=db)
        user_dir = get_user_upload_dir(user.id)
        file_path = os.path.join(user_dir, filename)

        if not os.path.exists(file_path):
            raise _fastapi.HTTPException(status_code=404, detail="File not found")

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)
        start = 0
        end = file_size - 1

        if range_header:
            range_match = re.match(r'bytes=(\d+)-(\d+)?', range_header)
            if range_match:
                start = int(range_match.group(1))
                if range_match.group(2):
                    end = int(range_match.group(2))
                else:
                    end = file_size - 1

        chunk_size = end - start + 1

        def iterfile():
            nonlocal chunk_size  # Ensure chunk_size is accessible in this scope
            with open(file_path, mode="rb") as file:
                file.seek(start)
                while chunk_size > 0:
                    chunk = file.read(min(4096, chunk_size))
                    if not chunk:
                        break
                    yield chunk
                    chunk_size -= len(chunk)

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "audio/mpeg",
        }

        return StreamingResponse(iterfile(), status_code=206, headers=headers)

    except Exception as e:
        raise _fastapi.HTTPException(status_code=500, detail=str(e))
    
# Testing the ci/cd functions because it doesn't work at all and that's it
