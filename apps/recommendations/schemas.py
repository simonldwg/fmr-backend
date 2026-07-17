from typing import Optional, List

from django.conf import settings
from ninja import Schema
from pydantic import Field, model_validator

from apps.library.feature_extraction.consts import GENRE_LITERAL
from apps.library.schemas import SongSchema


class RecommendationFeaturesSchema(Schema):
    valence: Optional[float] = None
    arousal: Optional[float] = None
    authenticity: Optional[float] = None
    timeliness: Optional[float] = None
    complexity: Optional[float] = None
    danceability: Optional[float] = None
    tonal: Optional[float] = None
    voice: Optional[float] = None
    bpm: Optional[float] = None

    @model_validator(mode="after")
    def check_at_least_one_feature(self):
        if all(
            getattr(self, field) is None
            for field in self.__class__.model_fields
        ):
            raise ValueError("Please provide at least one valid song feature to recommend a playlist")
        return self



class PlaylistRecommendationParametersSchema(Schema):
    length: int = Field(
        settings.DEFAULT_PLAYLIST_LENGTH,
        ge=settings.MIN_PLAYLIST_LENGTH,
        le=settings.MAX_PLAYLIST_LENGTH
    )
    features: RecommendationFeaturesSchema
    genre_filters: Optional[List[GENRE_LITERAL]] = None
    max_song_length_filter: Optional[int] = None



PlaylistSchema = List[SongSchema]

class PlaylistRecommendationResponseSchema(Schema):
    playlist: PlaylistSchema
    message: Optional[str] = None
