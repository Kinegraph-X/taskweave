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

        parser.add_argument('--log_level',
                            help='Logging verbosity (default: from .env or INFO)',
                            required=False,
                            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                            default=None
                            )
        # not implemented
        parser.add_argument('--debug', 
                            help='Enable CLI logging instead of HTTP server',
                            required=False,
                            action='store_true'
                            )
        # not implemented
        parser.add_argument('--dist', 
                            help='Define paths relative to dist folder',
                            required=False,
                            action='store_true'
                            )
        
        _args = parser.parse_args()

    return _args


def get_config():
    args = get_args()

    config.debug = args.debug
    config.dist = args.dist

    # CLI overrides .env only if arg explicitely given

    if args.log_level is not None:
        config.log_level = args.log_level

    return config, args