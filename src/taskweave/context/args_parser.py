import argparse

from .channel_info import extract_channel_info

from .config import config

_args = None

def get_args() -> argparse.Namespace :
    global _args
    if _args is None:
        parser = argparse.ArgumentParser(
            description='Parallelized, worker-based, transcription and matching engine (via Fast-Whisper) \n' \
            'Usage: python run_pipeline.py <m3u8_url> [-match] [keyword1] [keyword2...]')

        parser.add_argument('--path', '-i',
                            help='Path or URL to video/audio/m3u8/manifest file',
                            required=True,
                            nargs='+'
                            )
        parser.add_argument('--match', '-m',
                            help='Enable keyword matching. Add space-separated keywords',
                            required=False,
                            nargs='+'
                            )
        parser.add_argument('--chunk_size', '-t',
                            help='Chunk size in seconds when processing audio (default: 3600)',
                            required=False,
                            type=int,
                            default=None  # None to distinguish non-given from "given at default value"
                            )
        parser.add_argument('--whisper_model', '-w',
                            help='Whisper model size: tiny, base, small, medium, large (default: from .env or small)',
                            required=False,
                            choices=['tiny', 'base', 'small', 'medium', 'large'],
                            default=None
                            )
        parser.add_argument('--whisper_platform',
                            help='Whisper execution platform: cpu, cuda, mps (default: from .env or cpu)',
                            required=False,
                            choices=['cpu', 'cuda', 'mps'],
                            default=None
                            )
        parser.add_argument('--log_level',
                            help='Logging verbosity (default: from .env or INFO)',
                            required=False,
                            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                            default=None
                            )
        parser.add_argument('--debug', 
                            help='Enable CLI logging instead of HTTP server',
                            required=False,
                            action='store_true'
                            )
        parser.add_argument('--test', 
                            help='Use test m3u8 urls and mock whisper',
                            required=False,
                            action='store_true'
                            )
        parser.add_argument('--dist', 
                            help='Define paths relative to dist folder',
                            required=False,
                            action='store_true'
                            )
        
        _args = parser.parse_args()

    return _args


def get_config():
    args = get_args()

    if args.test:
        config.should_match = False
        config.whisper_path = f"{config.package_name}/{config.runners_foler}/whisper_mock.py"
        config.whisper_func = 'mock_transcription'

    config.debug = args.debug
    config.dist = args.dist

    if args.path:
        config.media_path = args.path[0]
        config.channel_name, config.vod_uid = extract_channel_info(args.path[0])
    else:
        config.channel_name = "test_channel"
        config.vod_uid = "local"

    if args.match:
        config.should_match = True
        config.keywords = args.match
    else:
        print(f"[INFO] : matching is not enabled, transcript only (add --match keyword1, keyword2, etc to enable)")

    # CLI overrides .env only if arg explicitely given
    if args.chunk_size is not None:
        config.segment_duration = args.chunk_size

    if args.whisper_model is not None:
        config.whisper_model = args.whisper_model

    if args.whisper_platform is not None:
        config.whisper_platform = args.whisper_platform

    if args.log_level is not None:
        config.log_level = args.log_level

    config.segment_duration = args.chunk_size

    return config, args