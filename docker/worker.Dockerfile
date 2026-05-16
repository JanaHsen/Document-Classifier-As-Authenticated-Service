# Owner: HADI
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

RUN chmod +x /app/docker/startup.sh

ENTRYPOINT ["/app/docker/startup.sh"]
CMD ["python", "-m", "app.workers.inference_worker"]
