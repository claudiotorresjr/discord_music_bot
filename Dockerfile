FROM python:3.7

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

COPY *.py /usr/src/bot/
COPY ./requirements.txt .
COPY ./run.sh .

RUN apt-get update && apt-get install -y ffmpeg

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "./run.sh" ]