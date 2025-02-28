# Use an official Python image as the base
FROM python:3.10-buster

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

RUN pip install --no-cache-dir git+https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/dazehead/Coinbase_Trader.git@db2bd1c55e431f2e7e2c1787b472bda8b5f89825#egg=coinbase_trader

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libatlas-base-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Download and install TA-Lib from the official source
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.4.0-src.tar.gz ta-lib

# Update linker cache to include TA-Lib
RUN ldconfig

# Install Python dependencies
COPY requirements2.txt /app/requirements2.txt
RUN pip install --no-cache-dir -r /app/requirements2.txt

# Copy application files
COPY .env /app/.env
COPY . /app
WORKDIR /app

# Copy the database into the image
COPY database /app/database

# Expose the port your application runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "core.webapp.app"]
