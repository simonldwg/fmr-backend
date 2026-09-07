from typing import List, Optional
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from ninja import File, Form, Router
from ninja.files import UploadedFile
from ninja.pagination import PageNumberPagination, paginate

from .models import Album, Song, SongFeatures, SongGenres
from .schemas import AlbumSchema, SongCreateSchema, SongSchema

from .methods import calculate_genres_and_features
from .schemas import AlbumDetailSchema

songs_router = Router(tags=["songs"])
albums_router = Router(tags=["albums"])


@albums_router.post("/", response=AlbumSchema)
def create_album(
    request,
    album_name: str = Form(...),
    artist: str = Form(...),
    artwork_file: Optional[UploadedFile] = File(None),
):
    if artwork_file and not artwork_file.name.endswith((".jpg", ".jpeg", ".png")):
        raise ValidationError("Unsupported file format. Please upload an image file.")

    # Check if the album already exists, if so, return it
    existing_album = Album.objects.filter(album_name=album_name, artist=artist).first()
    if existing_album:
        return existing_album

    album = Album.objects.create(album_name=album_name, artwork_file=artwork_file, artist=artist)
    return AlbumSchema.from_orm(album)


@albums_router.get("/", response=List[AlbumSchema])
@paginate(PageNumberPagination, page_size=10)
def list_albums(request, album_name: Optional[str] = None):
    qs = Album.objects.all()
    if album_name:
        qs = qs.filter(album_name__icontains=album_name)
    qs = qs.order_by(Lower("album_name"))
    return qs


@albums_router.get("/all", response=List[AlbumSchema])
def list_all_albums(request):
    return Album.objects.all().order_by(Lower("album_name"))


@albums_router.get("/{album_id}", response=AlbumDetailSchema)
def get_album_details(request, album_id: UUID):
    album = get_object_or_404(Album, id=album_id)
    return album


@albums_router.delete("/{album_id}")
def delete_album(request, album_id: UUID):
    album = get_object_or_404(Album, id=album_id)
    album.delete()
    return {"deleted": True}


@songs_router.post("/", response=SongSchema)
def create_and_upload_song(
    request,
    song: SongCreateSchema = Form(...),
    audio_file: UploadedFile = File(...),
):
    album = Album.objects.get(id=song.album_id)

    genres, features, duration_s = calculate_genres_and_features(audio_file)

    song = Song.objects.create(
        **song.model_dump(),
        features=SongFeatures.objects.create(**features.model_dump()),
        genres=SongGenres.objects.create(**genres.model_dump()),
        duration_s=duration_s,
        audio_file=audio_file,
        album=album,
    )

    return SongSchema.from_orm(song)


@songs_router.get("/", response=List[SongSchema])
@paginate(PageNumberPagination, page_size=10)
def list_songs(request, title: Optional[str] = None):
    qs = Song.objects.all()
    if title:
        qs = qs.filter(title__icontains=title)
    qs = qs.order_by(Lower("title"))
    return qs


@songs_router.get("/all", response=List[SongSchema])
def list_all_songs(request):
    return Song.objects.all().order_by(Lower("title"))


@songs_router.get("/{song_id}", response=SongSchema)
def get_song_details(request, song_id: UUID):
    song = get_object_or_404(Song, id=song_id)
    return song


@songs_router.delete("/{song_id}")
def delete_song(request, song_id: UUID):
    song = get_object_or_404(Song, id=song_id)
    song.delete()
    return {"deleted": True}
