#!/bin/bash

set -e

(cd challenge-base && docker build  . -t gcr.io/paradigmxyz/ctf/base:latest)
echo "building cairo"
(cd challenge && docker build . -f Dockerfile.cairo -t xxymboll/cairo:latest)
echo "building eth"
(cd challenge && docker build . -f Dockerfile.eth -t xxymboll/eth:latest)
echo "building solana"
(cd challenge && docker build . -f Dockerfile.solana -t xxymboll/solana:latest)
echo "building sui"
(cd challenge && docker build . -f Dockerfile.sui -t xxymboll/sui:latest)
