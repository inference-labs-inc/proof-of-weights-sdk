FROM --platform=linux/amd64 mcr.microsoft.com/devcontainers/base:jammy
RUN apt-get update && \
    apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    wget \
    fish \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install --upgrade pip
RUN pip3 install bittensor bittensor-cli yarl requests fastapi pydantic bpython ptpython
