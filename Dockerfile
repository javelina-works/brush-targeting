# Stage 1: Build the Vue Frontend
FROM node:18 AS frontend-builder
WORKDIR /app
COPY frontend/ .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN yarn install && yarn build


# Stage 2: Set Up the FastAPI Backend
FROM python:3.11-slim AS backend
WORKDIR /app


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

# Copy built frontend files into the backend's static directory
COPY --from=frontend-builder /app/dist frontend/dist

# Copy backend files
COPY backend/ ./backend/

# Set environment variable to production
ENV ENV=production

# Install the project now that the full directory is available
RUN poetry install --no-root

EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000" ]
