#!/bin/bash

# If we can't login, no reason to continue.
docker login

VERSION=$(grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)

/bin/bash ./ci.sh

docker buildx build . \
  -t "jacoby6000/chivalry2-unofficial-server-browser-discord-bot:$VERSION" \
  -t "jacoby6000/chivalry2-unofficial-server-browser-discord-bot:latest" \
  --push
