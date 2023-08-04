from ffmpeg.asyncio import FFmpeg
from scraper import without_extension

async def convert2mp4(filename):
    if not filename:
        return None

    converted_name = 'converted_' + without_extension(filename) + ".mp4"
    ffmpeg = FFmpeg().option("y").input(filename).output(converted_name,
                                   vcodec='libx264',
                                   pix_fmt='yuv420p',
                                   loglevel='quiet',
                                   **{'movflags': 'faststart',
                                      'vf': 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                                      'crf': '26'})

    await ffmpeg.execute()
    
    return converted_name
