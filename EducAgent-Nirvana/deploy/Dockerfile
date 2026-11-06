FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends nginx ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 educagent && useradd --uid 10001 --gid 10001 --no-create-home educagent
WORKDIR /app
COPY constraints.txt ./
COPY EducAgent-SDK ./EducAgent-SDK
RUN python -m pip install --no-cache-dir -c constraints.txt ./EducAgent-SDK
COPY . .
RUN mkdir /data && chown 10001:10001 /data
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DATA_DIR=/data BIND_HOST=0.0.0.0
USER 10001:10001
EXPOSE 9090
STOPSIGNAL SIGTERM
CMD ["python", "run.py"]
