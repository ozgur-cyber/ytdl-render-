FROM python:3.9

# Sunucuye FFmpeg (görüntü ve ses birleştirici) yüklüyoruz
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Render'ın dinamik port yapısına uyum sağlıyoruz
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
