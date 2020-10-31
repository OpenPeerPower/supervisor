#!/bin/bash
set -e

# Update frontend
git submodule update --init --recursive --remote

[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
cd open-peer-power-polymer
nvm install
script/bootstrap

# build frontend
cd oppio
./script/build_oppio

# Copy frontend
rm -rf ../../supervisor/api/panel/*
cp -rf build/* ../../supervisor/api/panel/
