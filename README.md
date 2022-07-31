# memes2telegram
[![CodeQL](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/codeql-analysis.yml)[![Dependency Review](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/dependency-review.yml)[![Pylint](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/pylint.yml/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/pylint.yml)

Simple Telegram chat bot which downloads GIF, WEBM, MP4 by URL and send it back as properly encoded Telegram MP4 video

Your bot should be added to group as admin(otherwise you should disable privacy mode for it)

## How to use

- Send message with media url mentioning bot name handle

> @memes2telegram https://img-9gag-fun.9cache.com/photo/ID.webm

- Bot will send converted media back to same chat and will delete(!) original message

## How to run

- Make sure you set your **BOT_TOKEN** in your **ENV**
- Install [FFMPEG](https://ffmpeg.org/download.html)

```
pip install -r requirements.txt
python main.py
```

JFYI: It can be hosted on Heroku
with [FFMPEG Buildpack](https://elements.heroku.com/buildpacks/jonathanong/heroku-buildpack-ffmpeg-latest)

## Supported memes:

- DTF mp4: https://leonardo.osnova.io/UUID/-/format/mp4/
- 9Gag webm: https://img-9gag-fun.9cache.com/photo/ID.webm
- 9Gag mp4: https://img-9gag-fun.9cache.com/photo/ID.mp4
- JoyReactor gifs: http://imgX.joyreactor.cc/pics/post/ID.gif
- JoyReactor posts: http://joyreactor.cc/post/ID (it will try to send all pics inside post as albums)
- Any downloadable link for GIF/MP4/WEBM should also work

## Roadmap and TODOs

- Convert videos in memory rather than working with files
- Instagram posts scraping
- Sending multiple albums bugfix
