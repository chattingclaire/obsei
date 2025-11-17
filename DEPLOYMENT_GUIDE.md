# 🚀 部署和运行指南

## 📋 系统要求

### 基础环境
- **Python**: 3.10 或更高版本
- **Node.js**: 18.0 或更高版本
- **操作系统**: Linux / macOS / Windows (推荐Linux)
- **内存**: 最低 4GB RAM
- **存储**: 最低 10GB 可用空间

### 必需服务
- **Supabase账号**: 用于数据库 (免费版即可)
- **Claude API密钥**: Anthropic API访问权限

### 可选服务 (提升功能)
- **ffmpeg**: 用于视频处理
- **Playwright浏览器**: 用于网页自动化

---

## 🔑 需要的API密钥和账号

### 1. **必需的** (系统核心功能)

#### Supabase (数据库)
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**如何获取:**
1. 访问 https://supabase.com
2. 创建免费账号
3. 创建新项目
4. 在 Settings → API 中找到：
   - `Project URL` → SUPABASE_URL
   - `anon public` → SUPABASE_KEY
   - `service_role` → SUPABASE_SERVICE_ROLE_KEY

#### Claude API (AI能力)
```bash
CLAUDE_API_KEY=sk-ant-xxxxx
```

**如何获取:**
1. 访问 https://console.anthropic.com
2. 注册账号
3. 在 API Keys 页面创建新密钥
4. 复制密钥 (以 `sk-ant-` 开头)

---

### 2. **推荐的** (增强数据采集)

#### GitHub (代码仓库)
```bash
GITHUB_TOKEN=ghp_xxxxx
```

**如何获取:**
1. 访问 https://github.com/settings/tokens
2. Generate new token (classic)
3. 勾选 `repo`, `read:user` 权限
4. 生成并复制 token

#### Twitter/X (社交媒体)
```bash
TWITTER_BEARER_TOKEN=xxxxx
```

**如何获取:**
1. 访问 https://developer.twitter.com
2. 创建开发者账号
3. 创建新App
4. 在 Keys and tokens 中找到 Bearer Token

#### Reddit (社区内容)
```bash
REDDIT_CLIENT_ID=xxxxx
REDDIT_CLIENT_SECRET=xxxxx
```

**如何获取:**
1. 访问 https://www.reddit.com/prefs/apps
2. Create App → script
3. 复制 client_id 和 secret

---

### 3. **可选的** (扩展功能)

```bash
# YouTube
YOUTUBE_API_KEY=xxxxx

# ProductHunt
PRODUCTHUNT_API_KEY=xxxxx

# Crunchbase
CRUNCHBASE_API_KEY=xxxxx

# Browserless (浏览器自动化云服务)
BROWSERLESS_API_KEY=xxxxx
BROWSERLESS_URL=https://chrome.browserless.io
```

---

## 📥 安装步骤

### 第一步：克隆仓库

```bash
# 克隆代码
git clone https://github.com/chattingclaire/obsei.git
cd obsei
```

### 第二步：配置环境变量

```bash
# 复制配置模板
cp config/.env.example config/.env
cp config/keys.env.example config/keys.env

# 编辑配置文件
nano config/keys.env  # 或使用你喜欢的编辑器
```

**在 config/keys.env 中填入你的API密钥:**

```bash
# 必需的
CLAUDE_API_KEY=sk-ant-你的密钥
SUPABASE_URL=https://你的项目.supabase.co
SUPABASE_KEY=你的anon-key
SUPABASE_SERVICE_ROLE_KEY=你的service-role-key

# 推荐的
GITHUB_TOKEN=ghp_你的token
TWITTER_BEARER_TOKEN=你的bearer-token
REDDIT_CLIENT_ID=你的client-id
REDDIT_CLIENT_SECRET=你的client-secret

# 可选的（如果有就填，没有就留空）
YOUTUBE_API_KEY=
PRODUCTHUNT_API_KEY=
CRUNCHBASE_API_KEY=
BROWSERLESS_API_KEY=
```

### 第三步：安装Python依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器（用于网页自动化）
playwright install chromium
```

### 第四步：设置Supabase数据库

```bash
# 方法1: 使用Supabase Web界面
# 1. 登录 https://supabase.com
# 2. 进入你的项目
# 3. 点击左侧 SQL Editor
# 4. 复制 database/schema.sql 的内容
# 5. 粘贴并运行

# 方法2: 使用psql命令行（如果有）
psql -h db.你的项目.supabase.co -U postgres -d postgres -f database/schema.sql
```

### 第五步：安装前端依赖

```bash
cd dashboard/frontend
npm install
cd ../..
```

---

## ▶️ 启动系统

### 方式一：完整启动（推荐用于生产）

```bash
# Terminal 1: 启动后端API
cd dashboard/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: 启动前端
cd dashboard/frontend
npm run dev

# Terminal 3: 启动Pipeline（可选）
python main.py --mode pipeline --continuous
```

### 方式二：简化启动（开发测试）

```bash
# 只启动API和前端，不运行pipeline
cd dashboard/backend
uvicorn main:app --reload &

cd ../frontend
npm run dev
```

### 方式三：单独测试Agent

```bash
# 测试Data Agent
python main.py --mode single-agent --agent data

# 测试Classify Agent
python main.py --mode single-agent --agent classify

# 测试Signal Agent
python main.py --mode single-agent --agent signal
```

---

## 🧪 验证测试

### 1. 检查后端API

打开浏览器访问: http://localhost:8000/docs

你应该看到 FastAPI 自动生成的 API 文档。

### 2. 检查前端

打开浏览器访问: http://localhost:3000

你应该看到多Agent智能平台的主界面。

### 3. 测试数据库连接

```bash
curl http://localhost:8000/health
```

应该返回:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-17T..."
}
```

### 4. 测试Agent列表

```bash
curl http://localhost:8000/agents/list
```

应该返回5个Agent的列表。

---

## 🎯 快速开始使用

### 步骤1：配置Data Agent

1. 访问 http://localhost:3000
2. 在左侧找到 "数据采集Agent" 配置
3. 启用你想要的信息源（如GitHub、Twitter）
4. 点击保存

### 步骤2：运行Data Agent采集数据

```bash
python main.py --mode single-agent --agent data
```

等待几分钟，让它采集数据到数据库。

### 步骤3：运行Classify Agent分类

```bash
python main.py --mode single-agent --agent classify
```

这会对采集的数据进行分类。

### 步骤4：开始对话！

1. 在前端界面选择一个Agent（如Signal Agent）
2. 输入问题："帮我找最近的AI项目"
3. Agent会查询知识库并回复你！

---

## 🔧 常见问题

### Q1: 缺少某些Python包
```bash
# 如果遇到缺失的包，单独安装
pip install 包名
```

### Q2: Supabase连接失败
- 检查 `config/keys.env` 中的URL和密钥是否正确
- 确保Supabase项目处于激活状态
- 检查防火墙是否阻止了连接

### Q3: Claude API调用失败
- 检查API密钥是否正确
- 确认账号有足够的credits
- 查看 https://console.anthropic.com 的使用情况

### Q4: 前端无法连接后端
- 确认后端运行在 http://localhost:8000
- 检查CORS设置
- 查看浏览器控制台的错误信息

### Q5: Playwright浏览器启动失败
```bash
# 重新安装浏览器
playwright install --with-deps chromium
```

---

## 📊 推荐的最小配置

**如果你刚开始测试，只需要：**

✅ **必需:**
- Supabase账号 + 数据库
- Claude API密钥

✅ **推荐:**
- GitHub Token (用于采集代码仓库)

其他的API可以后续添加！

---

## 🎬 完整示例配置

这是一个最小可用的 `config/keys.env`:

```bash
# 必需 - 核心功能
CLAUDE_API_KEY=sk-ant-api03-你的Claude密钥
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_KEY=eyJhbGci你的anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci你的service-role-key

# 推荐 - 增强功能
GITHUB_TOKEN=ghp_你的GitHub-token

# 其他可选
TWITTER_BEARER_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
YOUTUBE_API_KEY=
```

有了这些，系统就能运行！其他的API密钥可以后续逐步添加。

---

## 💡 小贴士

1. **开发阶段**: 只配置Supabase + Claude，测试基本功能
2. **扩展阶段**: 逐步添加GitHub、Twitter等API
3. **生产阶段**: 配置所有API，开启continuous模式

---

需要我帮你配置哪一部分？如果你已经有了API密钥，可以直接告诉我，我帮你检查配置是否正确！
