from typing import Pattern
import os, re
from dataclasses import dataclass
from .args_parser import get_config
config, args = get_config()

@dataclass
class Constants():
    ffmpeg_logs_folder = "ffmpeg_logs"
    chunks_folder = "chunks/"
    playlists_folder = "playlist/"
    playlist_basename = 'playlist_'
    playlist_ext = 'm3u8'
    audio_file = f"output_audio_{config.channel_name}_{config.vod_uid}"
    audio_ext = ".m4a"
    transcripts_folder = "transcripts"
    transcript_file = f"transcript_{config.channel_name}"
    transcript_ext = ".tsv"
    keywords_pattern : Pattern | None = re.compile(r"\b(" + "|".join(config.keywords) + r")\b", re.IGNORECASE) if config.keywords else None
    matching_script = f"{config.package_name}/{config.runners_foler}/match_keywords.py"
    match_folder = 'matches/'
    log_folder = "logs/"

constants = Constants()
os.makedirs(constants.ffmpeg_logs_folder, exist_ok=True)
os.makedirs(constants.chunks_folder, exist_ok=True)
os.makedirs(constants.transcripts_folder, exist_ok=True)
os.makedirs(constants.playlists_folder, exist_ok = True)
os.makedirs(constants.log_folder, exist_ok = True)

def get_app_context():
    return config, constants, args