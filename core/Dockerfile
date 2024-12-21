# Use an official Python image as the base
FROM python:3.10-buster

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
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY . /app
WORKDIR /app

# Expose the port your application runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "core.webapp.app"]
