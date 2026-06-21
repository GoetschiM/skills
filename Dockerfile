FROM python:3.12-slim

# Node.js + Git installiere
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/frontend
RUN npm install 2>&1 | tail -10
WORKDIR /app
RUN pip install --no-cache-dir pyyaml
EXPOSE 8000
CMD ["python3", "-u", "server/skills_mcp.py", "http"]
