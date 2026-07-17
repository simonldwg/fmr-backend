from ninja import Router

from apps.recommendations.recommender.methods import generate_playlist
from apps.recommendations.schemas import PlaylistRecommendationParametersSchema, PlaylistRecommendationResponseSchema

router = Router(tags=["recommendations"])


@router.post("/playlist", response=PlaylistRecommendationResponseSchema,  exclude_unset=True)
def recommend_playlist(request, recommendation_params: PlaylistRecommendationParametersSchema):
    playlist = generate_playlist(
        recommendation_params.length,
        recommendation_params.features,
        recommendation_params.genre_filters,
        recommendation_params.max_song_length_filter
    )

    if len(playlist) == 0:
        return {
            "playlist": playlist,
            "message": "No recommendation could be generated. This is probably because the song library is empty or you have set filters for which no song could be found within the library."
        }

    return {"playlist": playlist}
