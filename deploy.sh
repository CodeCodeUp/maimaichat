#!/bin/sh

# 脉脉自动发布系统 Docker 部署脚本
# 版本: 2.0 (简化版)

set -e

# 配置变量
CONTAINER_NAME="maimaichat-app"
IMAGE_NAME="maimaichat:latest"
PORT="5000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=== 脉脉自动发布系统 Docker部署 ==="
echo

# 检查root权限
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}错误：需要root权限运行${NC}"
    echo "请使用: sudo $0"
    exit 1
fi

# 安装Docker
install_docker() {
    if command -v docker > /dev/null 2>&1; then
        echo -e "${GREEN}Docker已安装: $(docker --version)${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}安装Docker...${NC}"
    
    # 使用阿里云镜像安装Docker
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/debian/gpg | apt-key add -
    
    # 检测系统版本
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    fi
    
    case $OS in
        ubuntu)
            # 添加阿里云Docker源
            echo "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        debian)
            echo "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        centos|rhel)
            # 使用阿里云CentOS源
            yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io
            ;;
        *)
            # fallback到官方脚本
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            ;;
    esac
    
    # 配置Docker镜像加速
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << 'DOCKEREOF'
{
    "registry-mirrors": [
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com",
        "https://mirror.baidubce.com"
    ]
}
DOCKEREOF
    
    # 启动Docker服务
    systemctl daemon-reload
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker安装完成${NC}"
}

# 检查项目文件
check_files() {
    echo -e "${YELLOW}检查项目文件...${NC}"
    
    for file in app.py requirements.txt Dockerfile; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}错误：缺少文件 $file${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}文件检查通过${NC}"
}

# 配置环境
setup_env() {
    echo -e "${YELLOW}配置环境...${NC}"
    
    # 创建数据目录
    mkdir -p data logs
    chmod 755 data logs
    
    # 创建环境配置
    if [ ! -f ".env" ]; then
        cat > .env << 'ENVEOF'
MAIMAI_ACCESS_TOKEN=your_maimai_access_token_here
ENVEOF
        echo -e "${YELLOW}已创建.env文件，请设置MAIMAI_ACCESS_TOKEN${NC}"
        printf "是否现在编辑？(y/N): "
        read -r reply
        if [ "$reply" = "y" ] || [ "$reply" = "Y" ]; then
            ${EDITOR:-nano} .env
        fi
    fi
}

# 构建镜像
build_image() {
    echo -e "${YELLOW}构建Docker镜像...${NC}"
    docker build -t $IMAGE_NAME .
    echo -e "${GREEN}镜像构建完成${NC}"
}

# 停止旧容器
stop_container() {
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo -e "${YELLOW}停止并删除旧容器...${NC}"
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
    fi
}

# 启动容器
start_container() {
    echo -e "${YELLOW}启动新容器...${NC}"
    
    # 读取环境变量
    if [ -f ".env" ]; then
        . ./.env
    fi
    
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:5000 \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -e MAIMAI_ACCESS_TOKEN="$MAIMAI_ACCESS_TOKEN" \
        -e FLASK_ENV=production \
        --restart unless-stopped \
        $IMAGE_NAME
    
    echo -e "${GREEN}容器启动成功${NC}"
}

# 检查服务状态
check_status() {
    echo -e "${YELLOW}检查服务状态...${NC}"
    sleep 3
    
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}✓ 服务运行正常${NC}"
        echo
        echo "=== 服务信息 ==="
        echo -e "${BLUE}容器状态:${NC}"
        docker ps | grep $CONTAINER_NAME
        echo
        echo -e "${GREEN}访问地址: http://localhost:$PORT${NC}"
        echo
        echo "=== 管理命令 ==="
        echo -e "${BLUE}查看日志:${NC} docker logs -f $CONTAINER_NAME"
        echo -e "${BLUE}重启服务:${NC} docker restart $CONTAINER_NAME" 
        echo -e "${BLUE}停止服务:${NC} docker stop $CONTAINER_NAME"
        echo -e "${BLUE}进入容器:${NC} docker exec -it $CONTAINER_NAME sh"
    else
        echo -e "${RED}✗ 服务启动失败${NC}"
        echo "查看错误日志:"
        docker logs $CONTAINER_NAME
        exit 1
    fi
}

# 主执行流程
main() {
    echo -e "${GREEN}开始部署...${NC}"
    
    install_docker
    check_files
    setup_env
    build_image
    stop_container
    start_container
    check_status
    
    echo
    echo -e "${GREEN}=== 部署完成 ===${NC}"
    echo -e "${BLUE}服务已在后台运行${NC}"
}

# 运行部署
main "$@"
