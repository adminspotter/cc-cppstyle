FROM python:3-slim

MAINTAINER Trinity Quirk

RUN useradd -u 9000 -r -s /bin/false app

WORKDIR /code
COPY . /usr/src/app

USER app
VOLUME /code

CMD ["python3", "/usr/src/app/analyze.py"]
