from typing import List, Tuple, Optional

import numpy as np
from annoy import AnnoyIndex
from sklearn.neighbors import KDTree

from apps.library.models import Song

from apps.library.feature_extraction.consts import GENRE_LITERAL
from ..schemas import PlaylistSchema, RecommendationFeaturesSchema


def get_song_id() -> List[str]:
    """
    Get all song IDs from the database
    :return: List of song IDs.
    """
    song_IDs = []
    for document in Song.objects.all():
        song_IDs.append(document.id)
    return song_IDs


def get_song_id_and_dimensions(
    genre_filters: Optional[List[GENRE_LITERAL]],
    max_song_length_filter: Optional[float],
    features: List[str],
) -> Tuple[List[str], List[List[float]]]:
    """
    Get song IDs and their corresponding dimensions from database
    :param max_song_length_filter: Maximum song duration in seconds
    :param genre_filters: Genres to filter for
    :param features: List of features
    :return: List containing song IDs and their dimensions.
    """

    song_IDs = []
    song_Dimensions = []

    if max_song_length_filter is not None:
        songs = Song.objects.filter(duration_s__lte=max_song_length_filter)
    else:
        songs = Song.objects.all()

    for song in songs:
        # Skip song if a genre filter is set and none of the genres are included in top3_genres.
        # This is inefficient but SQLite (Django's default database) does not support filtering JSONFields (such as
        # top3_genres) by key, hence a solution like this has to be used.
        if genre_filters is not None and set(song.genres.top3_genres).isdisjoint(genre_filters):
            continue

        song_IDs.append(song.id)
        song_features = song.features.to_dict(include=features)
        dimensions = list(song_features.values())
        song_Dimensions.append(dimensions)

    return song_IDs, song_Dimensions


def get_song_information(top_IDs: List[str]) -> PlaylistSchema:
    """
    Get song information from the database based on the top song IDs.
    :param top_IDs: List of top song IDs.
    :return: List of Song objects with detailed information.
    """
    playlist: PlaylistSchema = []

    for i, val in enumerate(top_IDs):
        song = Song.objects.filter(id=val).first()
        if song is None:
            continue

        playlist.append(song)

    return playlist


def generate_playlist(
    length: int,
    features: RecommendationFeaturesSchema,
    genre_filters: Optional[List[GENRE_LITERAL]] = None,
    max_song_length_filter: Optional[int] = None
) -> PlaylistSchema:
    """
    Generate a playlist based on the input vector and playlist type.
    :param max_song_length_filter: Filter for the length of the song in seconds
    :param length: The length of the playlist.
    :param features: Input vector of different kinds of features.
    :param genre_filters: A list of genres to filter for.
    :return: List of Song objects in the generated playlist.
    """

    # Use only features that are present in the features object
    features_search = [key for key, value in features.model_dump().items() if value is not None]

    song_id_dimensions = get_song_id_and_dimensions(genre_filters, max_song_length_filter, features_search)

    top_songs_ids = k_d_tree(data=song_id_dimensions, features=features, numClosestNeighbours=length)

    playlist = get_song_information(top_IDs=top_songs_ids)
    return playlist


def k_d_tree(
    data: Tuple[List[str], List[List[float]]],
    features: RecommendationFeaturesSchema,
    numClosestNeighbours: int,
) -> List[str]:
    """
    takes as input the id, dimensions and length of Playlist, returns the song ids of the closest neighbours
    :param data: List containing song IDs and their dimensions.
    :param features: Input vector for the query.
    :param numClosestNeighbours: Number of closest neighbours to find.
    :return: List of song IDs of the closest neighbours.
    """
    # knearest extrahiert die doppelte größe der eigentlichen playlist, um später doppelte artists entfernen zu können
    # data = [[songAdresse1, songAdresse2, ...], [[InputVector], [5DimVektor], [5DimVektor2], ...]]

    features = list(features.model_dump(exclude_none=True).values())

    data[1].insert(0, features)
    songList = []

    # ensure number of requested library is as big as the actual song list
    if numClosestNeighbours > len(data[0]):
        numClosestNeighbours = len(data[0])

    tree = KDTree(data[1], leaf_size=3)
    dist, ind = tree.query(data[1][:1], k=numClosestNeighbours + 1)
    ind = np.array(ind).flatten().tolist()

    # erase query point (is always 0th element in data array) queryPoint = InputVector
    for i, val in enumerate(ind):
        if val == 0:
            del ind[i]
            if len(ind) == 0:
                break

        # subtract array index and get the Songadress (subtract because inputVector is deleted)
        ind[i] = ind[i] - 1
        songList.append(data[0][ind[i]])

    return songList


def annoy(
    song_id_dimensions: Tuple[List[str], List[List[float]]],
    inputVector: List[float],
    numClosestNeighbours: int,
) -> List[str]:
    """
    Takes as input the id, dimensions and length of Playlist, returns the song ids of the closest neighbours
    :param song_id_dimensions: List containing song IDs and their dimensions.
    :param inputVector: Input vector for the query.
    :param numClosestNeighbours: Number of closest neighbours to find.
    :return: List of song IDs of the closest neighbours.
    """

    ids = song_id_dimensions[0]
    dimensions = song_id_dimensions[1]

    dimensions.insert(0, inputVector)
    songList = []

    dimension_length = len(dimensions[0])  # Length of item vector that will be indexed
    annoy = AnnoyIndex(dimension_length, "euclidean")
    for i, val in enumerate(dimensions):
        annoy.add_item(i, val)

    annoy.build(40)  # 10 trees
    ind = annoy.get_nns_by_item(0, numClosestNeighbours)

    # erase query point (is always 0th element in data array) queryPoint = InputVector
    for i, val in enumerate(ind):
        if val == 0:
            del ind[i]
        # subtract array index and get the Songadress (subtract because inputVector is deleted)
        ind[i] = ind[i] - 1
        songList.append(ids[ind[i]])

    return songList
