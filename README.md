# 🤖 复合多AI智能体股票团队分析系统

- 股市有风险，入市需谨慎！

## 项目致谢

本项目受以下开源项目启发：
- **Hikyuu量化框架**：[@fasiondog](https://github.com/fasiondog) | https://github.com/fasiondog/hikyuu
- **aiagents-stock项目**：[@oficcejo](https://github.com/oficcejo) | https://github.com/oficcejo/aiagents-stock

> 其他功能详细介绍请参考原项目：https://github.com/oficcejo/aiagents-stock

## B站视频教程

- [本地部署教程](https://www.bilibili.com/video/BV1qHFPz9EXY/)
- [Docker部署教程](https://www.bilibili.com/video/BV1j2FNz4EAi/)
- [股票知识讲解合集](https://www.bilibili.com/video/BV1Y2FGzzEeS/)
- [投资认知提升合集](https://www.bilibili.com/video/BV1ugBMBAEbW)
- [价值投资核心逻辑](https://www.bilibili.com/video/BV1eJfxBrEjZ)

## 新增功能

### ⭐ 超短线选股策略（2026.4.22）

基于技术面，资金面、市场情绪等多维度筛选超短线强势股票。

**筛选条件：**
- 涨幅要求：主板近3日累计涨幅5-10%，创业板10-20%
- 均线多头：连续3日5日线在10日线上方
- 成交量放大：3日内有倍量阳线
- 缺口未回补：近5-10日内存在向上跳空缺口
- 资金热度：3日主力净流入 > 1亿元
- 排除ST股票
- 市场情绪：涨停数作为正向因子

**核心功能：**
- 多数据源支持：Hikyuu > AKShare > 问财
- 流通盘比例：使用stockholder.research数据
- 定时执行：每日收盘后自动筛选

### ⭐ 宏观分析（2026.3.23）

**新增独立板块：国家统计局官方宏观数据 × A股行业映射 × 优质标的筛选**

- 📊 国家统计局官方数据直连 — GDP、CPI、PPI、PMI、M2等
- 🧠 AI多智能体分析 — 宏观、策略、行业、标的分析师
- 🏭 A股行业利好/利空映射
- 🎯 优质标的推荐

### ⭐ 低估值价值投资策略（2026.2.27）

**筛选条件：** 低PE (≤20) + 低PB (≤1.5) + 高股息 (≥1%) + 低负债 (≤30%)
- 排序：按流通市值从小到大
- 量化择时：RSI(14) > 70 触发卖出

### ⭐ 宏观周期分析（2026.2.27）

- 康波周期 × 美林投资时钟 × 中国政策分析
- 4位AI分析师协同研判

---

## 🚀 快速开始

### 部署方式选择

本系统支持两种部署方式：
- **🐳 Docker部署（推荐）**：一键启动，环境隔离，适合所有用户
- **💻 本地部署**：传统方式，适合开发者

---

## 🐳 方式一：Docker 部署（推荐）⭐️

### 优势
- ✅ 无需配置Python和Node.js环境
- ✅ 一键启动，开箱即用
- ✅ 环境隔离，不影响系统
- ✅ 跨平台支持（Windows/macOS/Linux）
- ✅ 自动重启，稳定可靠

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+（推荐）
- DeepSeek API Key

### 快速开始

#### 1. 安装 Docker
- **Windows/macOS**: 下载安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### 2. 配置环境变量
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

编辑 `.env` 文件，填入您的 DeepSeek API Key：
```env
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

#### 3. 启动服务

**国内用户推荐**（使用国内镜像源，构建速度快6倍+）：
```bash
# 使用国内源版Dockerfile构建
docker build -f "Dockerfile国内源版" -t agentsstock1 .
docker run -d -p 8503:8501 -v $(pwd)/.env:/app/.env --name agentsstock1 agentsstock1
```

**标准构建方式**：
```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 或使用标准 Dockerfile
docker build -t agentsstock1 .
docker run -d -p 8503:8501 -v $(pwd)/.env:/app/.env --name agentsstock1 agentsstock1
```

#### 4. 访问系统（为避免端口冲突，已将运行端口改为8503）
打开浏览器访问：http://localhost:8503

#### 5. 常用命令
```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

---

## 💻 方式二：本地部署

### 1. 环境要求
- Python 3.8+(微软store或官网，推荐3.12)
- Node.js 16+ (微软store或官网，pywencai需要)
- 稳定的网络连接（大陆网络请关闭vpn）
- DeepSeek API Key

### 2. 安装依赖
创建激活虚拟环境（powershell）并安装依赖
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 配置API

#### 方法一：使用环境变量文件（推荐）
1. 复制环境变量模板文件：
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# 或者使用命令
cp .env.example .env
```

2. 编辑 `.env` 文件，设置您的配置（也可在前端web界面-环境配置中设置）：
```env
# DeepSeek API配置（必需）
DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# AI模型名称（可选，支持OpenAI兼容模型）
# 常用：deepseek-chat, deepseek-reasoner, qwen-plus, gpt-4o
DEFAULT_MODEL_NAME=deepseek-chat

# Tushare配置（可选）- 作为降级数据源
TUSHARE_TOKEN=your_tushare_token       # 在 https://tushare.pro 注册获取

# 邮件通知配置（可选）- 用于实时监测和智策定时分析
EMAIL_ENABLED=false
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_authorization_code
EMAIL_TO=receiver@example.com

# Webhook通知配置（可选）- 用于实时监测和智策定时分析
WEBHOOK_ENABLED=false
WEBHOOK_TYPE=dingtalk  # 或 feishu
WEBHOOK_URL=your_webhook_url_here
WEBHOOK_KEYWORD=股票  # 钉钉自定义关键词，飞书可留空

# MiniQMT量化交易配置（可选）
MINIQMT_ENABLED=false
MINIQMT_ACCOUNT_ID=your_account_id
MINIQMT_HOST=127.0.0.1
MINIQMT_PORT=58610
```

#### 方法二：设置系统环境变量
您也可以直接在系统环境变量中设置：
- 变量名：`DEEPSEEK_API_KEY`
- 变量值：您的API密钥

**注意**：环境变量文件的优先级高于系统环境变量。

### 4. 启动系统
```bash
.\venv\Scripts\Activate.ps1
python run.py
```
或者直接运行：
```bash
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

### 5. 访问系统
打开浏览器访问：http://localhost:8501

### 6. 安装Hikyuu量化框架（可选，用于本地财务数据）
Hikyuu是本地量化框架，可以提供更丰富的财务数据。如需安装：
```bash
# 进入hikyuu目录
cd hikyuu

# 安装编译工具xmake（如未安装）
pip install xmake

# 编译并安装
python setup.py install

# Windows下可能还需要安装Visual Studio Build Tools
```

---

## 📜 免责声明

本系统仅供学习和研究使用，不构成投资建议。股票投资有风险，入市需谨慎。使用本系统进行投资决策的风险由用户自行承担。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

