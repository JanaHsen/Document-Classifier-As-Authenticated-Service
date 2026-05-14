FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true
COPY . /app
ENV PYTHONUNBUFFERED=1
COPY docker/startup.sh /app/docker/startup.sh
COPY docker/vault/bootstrap.py /app/docker/vault/bootstrap.py
RUN chmod +x /app/docker/startup.sh || true
ENTRYPOINT ["/bin/sh", "/app/docker/startup.sh"]
CMD ["/bin/sh", "-lc", "python -m app.workers.inference_worker"]
# Owner: HADI
