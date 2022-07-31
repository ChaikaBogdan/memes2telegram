import ffmpeg
from scraper import without_extension


def convert2mp4(filename):
    converted_name = 'converted_' + without_extension(filename) + ".mp4"
    (ffmpeg.input(filename).output(converted_name,
                                   vcodec='libx264',
                                   pix_fmt='yuv420p',
                                   loglevel='quiet',
                                   **{'movflags': 'faststart',
                                      'vf': 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                                      'crf': '26'}).overwrite_output().run())
    return converted_name
