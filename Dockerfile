FROM python:3.7

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

ADD ./discord_bot /usr/src/bot/discord_bot
COPY ./requirements.txt .

RUN apt-get update && apt-get install -y ffmpeg

RUN pip3 install -r requirements.txt