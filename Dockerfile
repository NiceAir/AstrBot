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
    libssl-dev \
    curl

RUN curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh

#RUN python -m pip install -r requirements.txt --no-cache-dir
RUN python -m pip install -r requirements.txt

#RUN python -m pip install socksio wechatpy cryptography --no-cache-dir
RUN python -m pip install socksio wechatpy cryptography 

EXPOSE 6185
EXPOSE 6186

CMD [ "python", "main.py" ]
