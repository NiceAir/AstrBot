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
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN python -m pip install uv
RUN uv pip install -r requirements.txt --no-cache-dir --system
RUN uv pip install socksio uv pyffmpeg pilk --no-cache-dir --system

# 释出 ffmpeg
RUN python -c "from pyffmpeg import FFmpeg; ff = FFmpeg();"

# add /root/.pyffmpeg/bin/ffmpeg to PATH, inorder to use ffmpeg
RUN echo 'export PATH=$PATH:/root/.pyffmpeg/bin' >> ~/.bashrc

RUN python -m pip install socksio wechatpy cryptography -i https://pypi.tuna.tsinghua.edu.cn/simple 
RUN python -m pip install pypinyin pymilvus -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 6185
EXPOSE 6186

CMD [ "python", "main.py" ]
