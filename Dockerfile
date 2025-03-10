FROM python:3.10-slim
WORKDIR /AstrBot

COPY . /AstrBot/

COPY cn-sources-ubuntu-debian.list  /etc/apt/sources.list
COPY pip.conf ~/.pip/pip.conf


RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

RUN python -m pip install -r requirements.txt --no-cache-dir

RUN python -m pip install socksio wechatpy cryptography --no-cache-dir

EXPOSE 6185
EXPOSE 6186

CMD [ "python", "main.py" ]
