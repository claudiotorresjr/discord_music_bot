FROM alpine:edge

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

COPY *.py /usr/src/bot/

# Install dependencies
RUN apk update \
    && apk add --no-cache \
    ca-certificates \
    ffmpeg \
    opus \
    python3 \
    py3-pip \
    libsodium-dev \
    # Install build dependencies
    && apk add --no-cache --virtual .build-deps \
    gcc \
    git \
    libffi-dev \
    make \
    musl-dev \
    python3-dev \
    # Install pip dependencies
    && pip3 install --no-cache-dir discord.py[voice] lyricsgenius youtube-dl \
    # Clean up build dependencies
    && apk del .build-deps

CMD [ "python3", "bot.py" ]