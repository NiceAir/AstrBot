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
    curl \
    ca-certificates \
    bash 



RUN python -m pip install uv
RUN uv pip install -r requirements.txt  --system
RUN uv pip install socksio uv pyffmpeg pilk  --system

# 释出 ffmpeg
RUN python -c "from pyffmpeg import FFmpeg; ff = FFmpeg();"

# add /root/.pyffmpeg/bin/ffmpeg to PATH, inorder to use ffmpeg
RUN echo 'export PATH=$PATH:/root/.pyffmpeg/bin' >> ~/.bashrc


EXPOSE 6185
EXPOSE 6186

CMD [ "python", "main.py" ]
