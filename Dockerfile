FROM python:3.13-slim

# Install system dependencies required for Tkinter and GUI applications
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk-dev \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# Create the directory for the SQLite database so it can be mounted as a volume
RUN mkdir -p /root/.digital_wallet

# Run the app
CMD ["uv", "run", "main.py"]
