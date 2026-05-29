FROM node:24-slim AS web-build

WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISK_VISION_MODE=DATA_COLLECTION
ENV DISK_VISION_API_HOST=0.0.0.0
ENV DISK_VISION_API_PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=web-build /app/web/dist /app/web/dist

EXPOSE 8000
CMD ["python", "main.py", "--web"]
