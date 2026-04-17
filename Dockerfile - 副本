# 使用官方Python镜像作为基础镜像
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim

# 设置时区环境变量
ENV TZ=Asia/Shanghai

# 使用Debian官方源
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    rm -rf /etc/apt/sources.list.d/* || true

# 设置工作目录
WORKDIR /app

# 安装基础依赖、中文字体和时区数据
RUN apt-get update && apt-get install -y \
    curl \
    tar \
    xz-utils \
    ca-certificates \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fontconfig \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js（使用npmmirror）
RUN NODE_VERSION=18.20.4 && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then NODE_ARCH="x64"; \
    elif [ "$ARCH" = "arm64" ]; then NODE_ARCH="arm64"; \
    else NODE_ARCH="$ARCH"; fi && \
    curl -fsSL https://registry.npmmirror.com/-/binary/node/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz -o /tmp/node.tar.xz && \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 && \
    rm /tmp/node.tar.xz && \
    ln -s /usr/local/bin/node /usr/local/bin/nodejs

# 验证安装
RUN node --version && npm --version

# 配置npm使用npmmirror镜像源
RUN npm config set registry https://registry.npmmirror.com/

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -i https://pypi.org/simple/ -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data && chmod 777 /app/data

# 暴露Streamlit默认端口
EXPOSE 8503

# 设置健康检查
HEALTHCHECK CMD curl --fail http://localhost:8503/_stcore/health || exit 1

# 启动应用
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]