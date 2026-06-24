FROM ubuntu:24.04

RUN apt update && apt install -y curl python3 python3-pip tini build-essential git && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/ctf

RUN python3 -m pip install --no-cache-dir --break-system-packages \
    Flask==3.1.0 gunicorn==23.0.0 pycryptodome==3.22.0

ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        BIN="sui-testnet-v1.74.0-ubuntu-aarch64.tgz"; \
    else \
        BIN="sui-testnet-v1.74.0-ubuntu-x86_64.tgz"; \
    fi && \
    curl -fsSLO --retry 5 --retry-delay 5 "https://github.com/MystenLabs/sui/releases/download/testnet-v1.74.0/$BIN" && \
    tar xzf "$BIN" -C /usr/local/bin/ --strip-components=1 && \
    rm "$BIN"

WORKDIR /home/ctf/

COPY challenge-sui/setup setup

# Pre-cache Move dependencies
RUN cd setup && sui move build 2>&1 || true
COPY challenge-sui/solver solver
COPY challenge-sui/frontend frontend
COPY challenge-sui/deploy .
COPY challenge-sui/ppow.py .

EXPOSE 8080

CMD ["tini", "-g", "--", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "8", "--access-logfile", "/var/log/ctf/proxy.access.log", "--error-logfile", "/var/log/ctf/proxy.error.log", "--capture-output", "--log-level", "debug", "chal:app"]
