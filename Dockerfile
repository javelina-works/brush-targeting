FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libglib2.0-0 \
    libexpat1 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using Poetry
RUN pip install poetry
COPY pyproject.toml poetry.lock README.md ./

# Install package dependencies separate from our package
RUN poetry install --no-root

# Copy the application code
COPY . /app
WORKDIR /app

# Install the project now that the full directory is available
RUN poetry install --only main

# Run the application
CMD ["poetry", "run", "panel", "serve", "brush_targeting/main.py", "--port", "5006", "--allow-websocket-origin=*"]

# Only if invoking Poetry's venv beforehand
# CMD ["panel", "serve", "main.py", "--port", "5006", "--allow-websocket-origin=*"]
