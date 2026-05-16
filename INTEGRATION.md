# SafeClaw Integration Guide

整合 Next.js UI (safeclaw-ui) 与 SafeClaw Python 后端 (streamlit_ui/safe_claw)

## 架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│   Next.js API    │────▶│   FastAPI       │
│   (Frontend)     │     │   (Proxy Layer)  │     │   (Backend)     │
│   Port: 3000    │     │   Rewrites       │     │   Port: 8000   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │   SafeClaw      │
                                                  │   Python Core   │
                                                  │   • Agents      │
                                                  │   • Skills      │
                                                  │   • Memory      │
                                                  │   • LLM Gateway │
                                                  └─────────────────┘
```

## 启动步骤

### 1. 启动 FastAPI 后端

```bash
cd /Users/nicole/workspace/github/a476678244/python_gallery/streamlit_ui
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw
python start_api.py
```

验证:
- API: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

### 2. 启动 Next.js 前端

```bash
cd /Users/nicole/workspace/github/a476678244/python_gallery/safeclaw-ui/my-app
npm run dev
```

访问: http://localhost:3000

## API 端点映射

| 功能 | 前端调用 | Next.js Rewrite | FastAPI 端点 |
|------|---------|-----------------|--------------|
| Chat Stream | `/api/chat/stream` | ✓ | `POST /chat/stream` |
| Skills | `/api/skills` | ✓ | `GET/POST /skills` |
| Sessions | `/api/sessions` | ✓ | `GET/POST/DELETE /sessions` |
| Health | `/api/health` | ✓ | `GET /health` |

## FastAPI 端点详情

### POST /chat/stream
SSE 流式聊天响应

**Request:**
```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "session_id": "sess-123",
  "enabled_skills": ["web-search"],
  "model": "gemma-4b",
  "stream": true
}
```

**SSE Events:**
- `type: thinking` - Agent 思考步骤
- `type: content` - 流式内容
- `type: done` - 完成信号
- `type: error` - 错误信息

### GET /skills
获取技能树

**Response:**
```json
{
  "tree": [...],
  "total": 56,
  "builtin": 5,
  "private": 2,
  "linked": 2
}
```

### GET /sessions
获取会话列表

**Response:**
```json
{
  "sessions": [...],
  "total": 10,
  "has_more": false
}
```

## 开发模式

### 热重载
FastAPI 和 Next.js 都支持热重载:
- FastAPI: `reload=True` (已配置)
- Next.js: `npm run dev` (自动)

### 调试

1. **检查 FastAPI 是否运行:**
```bash
curl http://localhost:8000/health
```

2. **测试 API 端点:**
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

3. **检查 Next.js 代理:**
```bash
curl http://localhost:3000/api/health
```

## SafeClaw 集成状态

| 组件 | 集成状态 | 说明 |
|------|---------|------|
| ChatAgent | ✅ 就绪 | 使用 `ChatAgent.stream_process()` |
| SkillsManager | ✅ 就绪 | 技能树读取和切换 |
| MemoryManager | 🔄 部分 | Session 存储在 Next.js 端 |
| LLM Gateway | ✅ 就绪 | 自动通过 `llm_service` |
| Tools | ⏳ 待实现 | 需要添加工具调用端点 |

## 下一步

1. **连接真实 SafeClaw**: 确保 `safe_claw` 模块正确加载
2. **添加认证**: JWT 或 Session 认证
3. **持久化**: 将 session/message 存储到数据库
4. **工具调用**: 添加 `/tools/execute` 端点
5. **文件上传**: 添加 multipart/form-data 支持

## 故障排除

### FastAPI 无法加载 safe_claw
检查 Python path:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### CORS 错误
FastAPI 已配置 CORS:
```python
allow_origins=["http://localhost:3000"]
```

### 代理不工作
检查 Next.js rewrites 配置:
```typescript
// next.config.ts
rewrites: [
  { source: '/api/chat/stream', destination: 'http://localhost:8000/chat/stream' }
]
```
