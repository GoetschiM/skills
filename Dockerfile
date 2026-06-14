FROM python:3.12-slim

WORKDIR /app

# Python-Dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skills-Repo kopiere (ohni .git, .venv, etc.)
COPY . /app/skills/

# MCP-Server
COPY server/ /app/server/

# Default ENV
ENV SKILLS_REPO_PATH=/app/skills
ENV PORT=8000

EXPOSE 8000

CMD ["python", "/app/server/skills_mcp.py", "http"]
