FROM python:3.10-slim
WORKDIR /AstrBot

COPY . /AstrBot/

COPY cn-sources-ubuntu-debian.list  /etc/apt/sources.list
RUN mv /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak


RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    gcc \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    ca-certificates \
    bash 


RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

#RUN python -m pip install uv
#RUN uv pip install -r requirements.txt  --system
#RUN uv pip install socksio uv pyffmpeg pilk  --system


RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install socksio  pyffmpeg pilk  -i https://pypi.tuna.tsinghua.edu.cn/simple

# 释出 ffmpeg
RUN python -c "from pyffmpeg import FFmpeg; ff = FFmpeg();"

# add /root/.pyffmpeg/bin/ffmpeg to PATH, inorder to use ffmpeg
RUN echo 'export PATH=$PATH:/root/.pyffmpeg/bin' >> ~/.bashrc


EXPOSE 6185
EXPOSE 6186

CMD [ "python", "main.py" ]



