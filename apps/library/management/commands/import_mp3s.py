"""
Django management command that recursively imports MP3 files into the music
library.

Required metadata is read from the MP3 ID3 tags via *mutagen*:
    - title        -> TIT2   (required)
    - artist       -> TPE1   (required)
    - album        -> TALB   (required)
    - album artist -> TPE2   (falls back to TPE1 if absent)
    - artwork      -> APIC   (optional; a warning is printed if missing)

Files without the required tags are reported and skipped. Files (artwork
and audio files) are copied into the respective media folders, following
the same behavior as regular uploads.

Usage:
    python manage.py import_music /path/to/music/folder
"""

import os
from typing import Optional, Tuple

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import get_valid_filename

from mutagen import File as MutagenFile

from apps.library.methods import calculate_genres_and_features
from apps.library.models import SongFeatures, SongGenres, Song, Album

AUDIO_EXTENSIONS = (".mp3",)


class Command(BaseCommand):
    help = (
        "Recursively import MP3 files from a folder into the music library."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "directory",
            type=str,
            help="Folder that is searched recursively for .mp3 files.",
        )

    def handle(self, *args, **options):
        root = options["directory"]
        if not os.path.isdir(root):
            raise CommandError(f"'{root}' is not a directory.")

        mp3_paths = self._collect_mp3_files(root)
        if not mp3_paths:
            self.stdout.write(self.style.WARNING("No MP3 files found."))
            return

        added = skipped = 0
        for path in mp3_paths:
            if self._import_file(path):
                added += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"Finished. Added: {added}, skipped: {skipped}.")
        )

    @staticmethod
    def _collect_mp3_files(root: str):
        paths = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if name.lower().endswith(AUDIO_EXTENSIONS):
                    paths.append(os.path.join(dirpath, name))
        return sorted(paths)

    def _import_file(self, path: str) -> bool:
        metadata, error = self._read_metadata(path)
        if metadata is None:
            self.stderr.write(self.style.ERROR(f"Skipping '{path}': {error}"))
            return False

        # Skip songs that are already in the library
        if Song.objects.filter(
            title=metadata["title"], artist=metadata["artist"]
        ).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping '{path}': '{metadata['title']}' by "
                    f"{metadata['artist']} is already in the library."
                )
            )
            return False

        try:
            # Read the file into memory and wrap it so it exposes the same
            # interface the API endpoint receives from an HTTP upload
            # (.name and .file.read()).
            with open(path, "rb") as fh:
                upload = SimpleUploadedFile(
                    name=os.path.basename(path),
                    content=fh.read(),
                    content_type="audio/mpeg",
                )

            genres, features, duration_s = calculate_genres_and_features(upload)

            with transaction.atomic():
                album = self._get_or_create_album(metadata)
                song = Song.objects.create(
                    title=metadata["title"],
                    artist=metadata["artist"],
                    duration_s=duration_s,
                    features=SongFeatures.objects.create(**features.model_dump()),
                    genres=SongGenres.objects.create(**genres.model_dump()),
                    album=album,
                    audio_file=upload,  # -> saved into MEDIA_ROOT/Audio/
                )
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f"Skipping '{path}': import failed ({exc}).")
            )
            return False

        self.stdout.write(
            self.style.SUCCESS(f"Added '{song.title}' by {song.artist}.")
        )
        return True

    @staticmethod
    def _get_or_create_album(metadata: dict) -> Album:
        album = Album.objects.filter(
            album_name=metadata["album"], artist=metadata["album_artist"]
        ).first()
        if album:
            return album

        artwork = None
        if metadata["artwork"]:
            data, ext = metadata["artwork"]
            filename = get_valid_filename(f"{metadata['album']}{ext}")
            artwork = ContentFile(data, name=filename)

        return Album.objects.create(
            album_name=metadata["album"],
            artist=metadata["album_artist"],
            artwork_file=artwork,
        )

    def _read_metadata(self, path: str) -> Tuple[Optional[dict], Optional[str]]:
        try:
            audio = MutagenFile(path)
        except Exception as exc:
            return None, f"could not read audio file ({exc})"

        if audio is None or audio.tags is None:
            return None, "file is not tagged (no ID3 tags found)"

        tags = audio.tags
        title = self._text(tags, "TIT2")
        artist = self._text(tags, "TPE1")
        album = self._text(tags, "TALB")
        album_artist = self._text(tags, "TPE2") or artist

        missing = [
            label
            for label, value in (
                ("title", title),
                ("artist", artist),
                ("album", album),
            )
            if not value
        ]
        if missing:
            return None, f"missing required tag(s): {', '.join(missing)}"

        artwork = self._artwork(tags)
        if artwork is None:
            self.stdout.write(
                self.style.WARNING(f"'{path}': no embedded artwork found.")
            )

        return (
            {
                "title": title,
                "artist": artist,
                "album": album,
                "album_artist": album_artist,
                "artwork": artwork,
            },
            None,
        )

    @staticmethod
    def _text(tags, frame_id: str) -> Optional[str]:
        frame = tags.get(frame_id)
        if frame is None:
            return None
        text = str(frame).strip()
        return text or None

    @staticmethod
    def _artwork(tags) -> Optional[Tuple[bytes, str]]:
        if not hasattr(tags, "getall"):
            return None
        for frame in tags.getall("APIC"):
            if getattr(frame, "data", None):
                ext = ".png" if frame.mime == "image/png" else ".jpg"
                return frame.data, ext
        return None
