FROM python:3.11-slim

# Install git and other utilities needed by Jules to run commands
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the Python daemon
CMD ["python", "-u", "fde_daemon.py"]
