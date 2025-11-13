# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim
LABEL maintainer="analyser <analyser@gmail.com>"

# 设置工作目录
WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目文件
COPY pyproject.toml ./
COPY main.py ./
COPY dianplus/ ./dianplus/

# 使用 uv 安装依赖
RUN uv pip install --system --no-cache -e .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 运行主程序
CMD ["python", "main.py"]
