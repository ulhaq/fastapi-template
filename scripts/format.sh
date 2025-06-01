#!/bin/sh -e
set -x

ruff check src scripts --fix
ruff check src --select I --fix
ruff format src scripts