# SafeClaw Architecture

## 企业级 Feature-Based Architecture

> Business first, Domain second, UI third, Framework last

## 目录结构

```
src/
├── app/                      # Next.js App Router
│   ├── page.tsx             # 薄路由层 - 仅返回 <ChatWorkspace />
│   ├── layout.tsx           # 根布局
│   └── api/                 # API 路由
│       ├── chat/stream/
│       ├── sessions/
│       └── skills/
│
├── features/                 # 业务功能模块
│   ├── chat/                # Chat 功能
│   │   ├── components/      # Chat 专用组件
│   │   ├── services/        # Chat API 服务
│   │   └── hooks/           # Chat 专用 hooks
│   │
│   ├── agent/               # Agent 运行时功能
│   │   ├── components/      # Execution graph, thinking UI
│   │   ├── services/        # Agent execution services
│   │   ├── execution/       # 执行流管理
│   │   └── reasoning/       # 推理步骤管理
│   │
│   ├── skills/              # Skill 管理功能
│   │   ├── components/      # Skill tree UI
│   │   ├── services/        # Skill API 服务
│   │   └── runtime/         # Skill 运行时
│   │
│   ├── sidebar/             # Sidebar 功能
│   │   └── components/      # Session list, navigation
│   │
│   ├── workspace/           # Workspace 管理
│   │   ├── projects/        # 项目管理
│   │   ├── threads/         # 线程管理
│   │   └── context/         # 上下文管理
│   │
│   └── settings/            # 设置功能
│
├── entities/                 # 领域模型 (Domain Models)
│   ├── message/
│   │   ├── model.ts         # Message entity, types, factories
│   │   └── index.ts
│   ├── session/
│   │   ├── model.ts         # Session entity
│   │   └── index.ts
│   ├── skill/
│   │   ├── model.ts         # Skill entity
│   │   └── index.ts
│   ├── execution/
│   │   ├── model.ts         # Execution graph entity
│   │   └── index.ts
│   ├── model/
│   │   └── model.ts         # AI Model entity
│   │
│   └── index.ts             # 统一导出
│
├── stores/                   # 状态管理 (按职责拆分)
│   ├── ui-store.ts          # UI 状态 (sidebar, theme, modals)
│   ├── session-store.ts     # Session 业务状态
│   ├── message-store.ts     # Message 业务状态
│   ├── skill-store.ts       # Skill 业务状态
│   ├── execution-store.ts   # Execution 业务状态
│   └── index.ts             # 统一导出
│
├── shared/                   # 共享资源
│   ├── components/
│   │   ├── ui/              # 基础 UI 组件 (Switch, Button)
│   │   ├── layout/          # 布局组件
│   │   └── feedback/        # 反馈组件 (Toast, Alert)
│   │
│   ├── hooks/               # 通用 hooks
│   ├── utils/               # 工具函数
│   │   └── cn.ts           # className 合并
│   ├── constants/           # 常量
│   ├── types/               # 共享类型
│   └── config/              # 配置文件
│
├── providers/              # 全局 Providers
│   └── query-provider.tsx  # TanStack Query Provider
│
└── config/                 # 应用配置
    ├── models.config.ts
    ├── skills.config.ts
    └── feature-flags.ts
```

## 架构原则

### 1. Business-First Organization

按**业务功能**组织代码，而非 UI 形态：

```typescript
// ✅ Good - Feature-based
features/
  ├── chat/
  ├── agent/
  ├── skills/

// ❌ Bad - Component-based
components/
  ├── button/
  ├── sidebar/
  ├── chat-input/
```

### 2. Domain Models (entities/)

领域模型是核心业务对象：

```typescript
// entities/message/model.ts
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  metadata?: MessageMetadata;
}

// Factory functions
export function createUserMessage(content: string): Message {
  return {
    id: crypto.randomUUID(),
    role: 'user',
    content,
    timestamp: new Date(),
  };
}
```

### 3. Service Layer

所有 API 调用封装在 services：

```typescript
// features/chat/services/chat-api.ts
export class ChatService {
  async streamChat(request: ChatRequest, callbacks: ChatCallbacks): Promise<void> {
    // SSE handling, retry logic, error handling
  }
}

export const chatService = new ChatService();
```

### 4. Store Separation

按职责拆分 store，而非单一 store：

```typescript
// stores/ui-store.ts - UI 状态
// stores/session-store.ts - Session 业务
// stores/message-store.ts - Message 业务
// stores/skill-store.ts - Skill 业务
// stores/execution-store.ts - Execution 业务
```

### 5. Thin Page Layer

Page 只负责路由，无业务逻辑：

```typescript
// app/page.tsx
export default function Home() {
  return <ChatWorkspace />;
}
```

## 依赖规则

```
page.tsx
  ↓ (imports)
features/workspace (composition root)
  ↓
features/* (business features)
  ↓
stores/* (state management)
  ↓
services/* (API layer)
  ↓
entities/* (domain models)
```

**禁止反向依赖**：
- ❌ entities 不能依赖 stores
- ❌ services 不能依赖 components
- ❌ shared 不能依赖 features

## 当前功能

| Feature | Status |
|---------|--------|
| Chat streaming | ✅ |
| Session management | ✅ |
| Skill tree | ✅ |
| Execution graph | ✅ |
| Message history | ✅ |
| Sidebar navigation | ✅ |
| Responsive layout | ✅ |

## 下一步

1. **Config layer** - 添加配置文件
2. **Authentication** - 用户认证
3. **Real backend** - 连接 Python FastAPI
4. **Tests** - 单元测试和 E2E

## 参考

- [Feature-Sliced Design](https://feature-sliced.design/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
