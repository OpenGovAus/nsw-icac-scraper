import os
import re
import sys
import argparse
import shutil
import asyncio
from pathlib import Path


from . import scraper
from .folder_manager import verify_dir


if(sys.platform == 'win32'):
    if(shutil.which('ffmpeg.exe') is not None):
        FFMPEG = 'ffmpeg.exe'
else:
    if(shutil.which('ffmpeg') is not None):
        FFMPEG = 'ffmpeg'

NSW_ICAC_INVESTIGATION_RE = r'https?:\/\/(?:www\.)?icac\.nsw\.gov\.au\/investigations\/current-investigations\/[0-9]{4}\/[a-zA-Z0-9\-]+\/?(?:[a-zA-Z0-9\-]+)?$'


async def main():
    loop = asyncio.get_event_loop()
    USAGE_MSG = 'nsw_icac_scraper -o [Output Directory] [Investigation URL(s)]'
    parser = argparse.ArgumentParser(description='Download documents from NSW ICAC investigations.', usage=USAGE_MSG)
    parser.add_argument('-o', dest='output_dir', type=str, help='Output directory for downloaded content.')
    args, unknown = parser.parse_known_args()
    if(not args.output_dir):
        print('Output directory (-o) is required.')
        sys.exit(USAGE_MSG)
    else:
        args.output_dir = Path(args.output_dir)
        verify_dir(args.output_dir)

    exit_msg = 'Please provide at least 1 valid investigation URL.'
    if len(unknown) > 0:
        index = 1
        url_list = []
        for x in unknown:
            if re.match(NSW_ICAC_INVESTIGATION_RE, x) and x not in url_list:
                url_list.append(x)

        if len(url_list) > 0:
            for investigation in url_list:
                await scraper.download(investigation, args.output_dir)
        else:
            sys.exit(exit_msg)
    else:
        sys.exit(exit_msg)
