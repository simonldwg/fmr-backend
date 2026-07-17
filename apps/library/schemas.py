from typing import Annotated, Dict, Optional, TypeVar, Union
from uuid import UUID

from ninja import Schema
from pydantic import WrapValidator
from pydantic_core import PydanticUseDefault


def _empty_str_to_default(v, handler, info):
    if isinstance(v, str) and v == "":
        raise PydanticUseDefault
    return handler(v)


T = TypeVar("T")
EmptyStrToDefault = Annotated[T, WrapValidator(_empty_str_to_default)]


class AlbumSchema(Schema):
    id: UUID
    album_name: str
    artist: str
    artwork_url: Optional[str]


class SongFeaturesSchema(Schema):
    valence: float
    arousal: float
    authenticity: float
    timeliness: float
    complexity: float
    danceability: float
    tonal: float
    voice: float
    bpm: float


class SongGenresSchema(Schema):
    top3_genres: Dict[str, float] = {}
    all_genres: Dict[str, float] = {}


class SongSchema(Schema):
    id: UUID
    title: str
    album: Optional[AlbumSchema] = None
    artist: str
    duration_s: float
    features: SongFeaturesSchema
    genres: SongGenresSchema
    song_url: Optional[str]
    artwork_url: Optional[str]


class SongCreateSchema(Schema):
    title: str
    album_id: Optional[Union[UUID, str]] = None
    artist: str


class AlbumDetailSchema(AlbumSchema):
    songs: Optional[list[SongSchema]] = None
