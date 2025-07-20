FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y python3 python3-venv \
    libmagic1 file libglib2.0-dev libpango1.0-dev libpangocairo-1.0-0 \
    libcairo2 libffi-dev shared-mime-info ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python -m venv .venv

RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD [".venv/bin/gunicorn", "-w", "1", "-k", "gthread", "--threads", "1", "-b", "0.0.0.0:5000", "run:app"]
