# memes2telegram
[![CodeQL](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/github-code-scanning/codeql) [![Tests](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/tests.yml/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/tests.yml)

Simple Telegram chat bot that downloads GIF, WEBM, and MP4 by URL and sends them back as properly encoded Telegram MP4 videos.

Your bot should be added to a group as an admin (otherwise you should disable privacy mode for it).

## How to use

- Send a message with the media URL, mentioning the bot's name handle.

> @memes2telegram https://img-9gag-fun.9cache.com/photo/ID.webm

- The bot will send the converted media back to the same chat and will delete(!) the original message.

## How to run

- Make sure you set your **BOT_TOKEN** and **DOPAMINE_ID** in your **ENV** or **.env** file.
- Install [FFMPEG](https://ffmpeg.org/download.html)
- Install [Redis](https://redis.io/docs/install/install-redis/install-redis-on-linux/)
- Install [fortune-mod](https://github.com/shlomif/fortune-mod)
- Install [cowsay](https://itsfoss.com/cowsay/)
- Install the required dependencies and run the bot.

```
pip install poetry
poetry install --no-root
poetry run python main.py
```
## Docker

- `docker build -t memes2telegram .`
- `docker run -e BOT_TOKEN=XXX -e DOPAMINE_ID=XXX -d --name memes2telegram memes2telegram`

**JFYI:** It can be hosted on Heroku with [FFMPEG Buildpack](https://elements.heroku.com/buildpacks/jonathanong/heroku-buildpack-ffmpeg-latest).

## Supported memes:

- DTF mp4: `https://leonardo.osnova.io/UUID/-/format/mp4/`
- 9Gag webm: `https://img-9gag-fun.9cache.com/photo/ID.webm`
- 9Gag mp4: `https://img-9gag-fun.9cache.com/photo/ID.mp4`
- JoyReactor gifs: `http://imgX.joyreactor.cc/pics/post/ID.gif`
- JoyReactor posts: `http://joyreactor.cc/post/ID` (it will try to send all pics inside the post as albums)
- Instagram reels: `https://www.instagram.com/reel/XXXXX/`
- Any downloadable link for GIF/MP4/WEBM should also work.

## Supported commands:
- `/sword` - Get your daily sword measurement (knights only)
- `/fortune` - Receive your daily fortune cookie

## Roadmap and TODOs

- Convert videos in memory rather than working with files.
- Make it truly async (currently the conversion is blocking the bot).
