FROM xxymboll/sui:latest

COPY deploy/ /home/ctf/

COPY setup /home/ctf/setup

RUN true \
    && cd /home/ctf \
    && pip install -r requirements.txt --break-system-packages \
    && rm -rf /home/ctf/setup/build /home/ctf/setup/Move.lock \
    && mkdir -p /tmp/sui-build-home \
    && HOME=/tmp/sui-build-home sui move build --path /home/ctf/setup --default-move-flavor sui \
    && rm -rf /tmp/sui-build-home \
    && true
