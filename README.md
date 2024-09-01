# memes2telegram
[![CodeQL](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/github-code-scanning/codeql) [![Tests](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/tests.yml/badge.svg)](https://github.com/ChaikaBogdan/memes2telegram/actions/workflows/tests.yml)

Simple Telegram chat bot that downloads GIF, WEBM, and MP4 by URL and sends them back as properly encoded Telegram MP4 videos.

Your bot should be added to a group as an admin (otherwise you should disable privacy mode for it).

## How to use

- Send a message with the media URL, mentioning the bot's name handle.

```
> @memes2telegram https://img-9gag-fun.9cache.com/photo/ID.webm
```

- The bot will send the converted media back to the same chat and will delete(!) the original message.

## How to run

- Make sure you set your **BOT_TOKEN** in your **ENV** or **.env** file.
- Install [FFMPEG](https://ffmpeg.org/download.html)
- Install [fortune-mod](https://github.com/shlomif/fortune-mod) and fortunes* packages
- Install [cowsay](https://itsfoss.com/cowsay/)
- Install [figlet](http://www.figlet.org/)
- Install the required dependencies using [Poetry](https://python-poetry.org/docs/) and run the bot.

```
pip install poetry
poetry install --no-root
poetry run python main.py
```

## Docker

You will need supply absolute path to project on mounting the volume

```
docker build -t memes2telegram .
docker run -v d:/memes2telegram:/bot -e BOT_TOKEN=XXX --name memes2telegram -d memes2telegram run python main.py
# docker run --rm -v d:/memes2telegram:/bot memes2telegram lock
# docker run --rm -v d:/memes2telegram:/bot memes2telegram add httpx
# docker run --rm -v d:/memes2telegram:/bot memes2telegram add -G dev pytest_httpx
# docker run --rm -v d:/memes2telegram:/bot memes2telegram run ruff check --output-format=github .
# docker run --rm -v d:/memes2telegram:/bot memes2telegram run pytest -n auto
```

## Supported memes:

- DTF mp4: `https://leonardo.osnova.io/<ID>/-/format/mp4/`
- 9Gag webm: `https://img-9gag-fun.9cache.com/photo/<ID>.webm`
- 9Gag mp4: `https://img-9gag-fun.9cache.com/photo/<ID>.mp4`
- JoyReactor gifs: `http://imgX.joyreactor.cc/pics/post/<ID>.gif`
- JoyReactor posts: `http://joyreactor.cc/post/<ID>/` (it will try to send all pics inside the post as albums)
- Instagram reels: `https://www.instagram.com/reel/<ID>/`
- Instagram albums: `https://www.instagram.com/p/<ID>/`
- YouTube shorts and videos
- Tiktok videos
- Any downloadable link for GIF/MP4/WEBM should also work.

## Supported commands:
- `/sword` - Get your daily sword measurement (knights only)
- `/fortune` - Receive your daily fortune cookie
- `/nsfw` - Send scroll-height curtain to hide NSFW content above
