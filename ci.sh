#!/bin/bash

poetry install --no-root
poetry run mypy src
