FROM python:3.11-slim

WORKDIR /app

# 使用国内镜像源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y \
    gcc \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 使用清华大学PyPI镜像
COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs data

EXPOSE 5000

ENV PYTHONPATH=/app
ENV FLASK_ENV=production
ENV TZ=Asia/Shanghai

CMD ["python", "app.py"]