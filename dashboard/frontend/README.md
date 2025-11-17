# Multi-Agent Intelligence Dashboard - Frontend

Next.js 14 前端应用，为多Agent智能平台提供美观的聊天界面。

## 功能特性

### 🤖 Agent聊天界面
- **3个可对话的Agents**:
  - 📡 **Signal Agent**: 生成小红书风格信号，查询知识库
  - 💡 **Insight Agent**: 投资洞察分析，趋势报告
  - 💼 **Venture Agent**: 投资推荐，创始人研究

### ⚙️ 后台Agent监控
- 实时显示Data Agent和Classify Agent的运行状态
- 处理项目计数和状态指示
- 自动刷新状态

### 📊 知识库统计
- 实时显示原始数据、分类项、信号、洞察和投资机会的数量
- 每30秒自动更新

### 💬 聊天功能
- 完整的对话历史记录
- 自动查询知识库选项
- 快捷提示按钮
- 美观的消息气泡样式
- 加载状态动画
- 清空历史功能

## 安装和运行

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start
```

访问 http://localhost:3000

## 环境要求

- Node.js 18+
- 后端API运行在 http://localhost:8000

## 技术栈

- **Next.js 14**: React框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **Axios**: HTTP客户端
- **Supabase JS SDK**: 数据库客户端（可选）

## 组件说明

### AgentChat
主聊天组件，支持:
- 发送和接收消息
- 显示聊天历史
- 加载状态
- 自动查询知识库选项

### AgentSelector
Agent选择器，显示:
- 可对话的Agents列表
- 当前选中的Agent
- Agent描述和能力

### PipelineMetrics
显示知识库统计数据:
- 原始数据数量
- 已分类项目
- 生成的信号
- 洞察报告
- 投资机会

## 使用说明

1. **选择Agent**: 从左侧边栏选择要对话的Agent
2. **输入问题**: 在底部输入框输入您的问题
3. **查看回复**: Agent会基于知识库和工具回复您
4. **快捷提示**: 点击快捷提示按钮快速输入常用问题
5. **知识库查询**: 开启"自动查询知识库"以获得更准确的答案

## API集成

所有API调用都通过 http://localhost:8000:

- `POST /chat/{agent_name}`: 发送消息给Agent
- `GET /chat/{agent_name}/history`: 获取聊天历史
- `DELETE /chat/{agent_name}/history`: 清空聊天历史
- `GET /agents/list`: 获取Agent列表
- `GET /agents/status`: 获取Agent状态
- `GET /metrics/pipeline`: 获取管道指标

## 自定义

### 修改主题颜色
编辑 `tailwind.config.ts` 中的颜色配置

### 添加新的快捷提示
编辑 `src/components/AgentChat.tsx` 中的 `quickPrompts` 对象

### 修改刷新间隔
编辑各组件中的 `setInterval` 调用
