from sqlalchemy import Table, Column, ForeignKey, String
from database import Base

albums_photo_association_table = Table('albums_photos', Base.metadata,
                                       Column('album_id', String, ForeignKey('albums.id'), primary_key=True),
                                       Column('photo_id', String, ForeignKey('photos.id'), primary_key=True)
                                       )
