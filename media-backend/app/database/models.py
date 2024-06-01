import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash
import app.database.database as _database

class Media (_database.Base):
    __tablename__ = "media_table"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    title = _sql.Column(_sql.String, index=True)
    artist_id = _sql.Column(_sql.Integer, _sql.ForeignKey('artist_table.id'))
    time = _sql.Column(_sql.DateTime)
    album_id = _sql.Column(_sql.Integer, _sql.ForeignKey('album_table.id'), index=True)
    users_id = _sql.Column(_sql.Integer, _sql.ForeignKey('users_table.id'), index=True)
    length = _sql.Column(_sql.Integer)
    genre = _sql.Column(_sql.String, nullable=True)
    cover_image = _sql.Column(_sql.String, nullable=True)  # New field for cover image

    artist = _orm.relationship("Artist", back_populates="media")
    album = _orm.relationship("Album", back_populates="media")
    user = _orm.relationship("User", back_populates="media")

class Artist (_database.Base):
    __tablename__ = "artist_table"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, index=True, unique= True)

    media = _orm.relationship("Media", back_populates="artist")


class Album (_database.Base):
    __tablename__ = "album_table"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String, index=True, unique=True)

    media = _orm.relationship("Media", back_populates="album")


class User (_database.Base):
    __tablename__ = "users_table"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String, unique=True, index=True)
    hashed_password = _sql.Column(_sql.String)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

    media = _orm.relationship("Media", back_populates="user")
    posts = _orm.relationship("Post", back_populates="owner")

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)

class Post (_database.Base):
    __tablename__ = "posts"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    owner_id = _sql.Column(_sql.Integer, _sql.ForeignKey("users_table.id"))
    post_text = _sql.Column(_sql.String, index=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

    owner = _orm.relationship("User", back_populates="posts")