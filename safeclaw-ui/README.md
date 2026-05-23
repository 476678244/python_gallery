# SafeClaw UI - Premium Agent Workspace

Production-grade AI Agent Workspace UI built with Next.js, React, TypeScript, Tailwind CSS, and shadcn/ui.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 16 (App Router) |
| UI Library | React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS 4 |
| Components | shadcn/ui + Radix UI |
| Animation | Framer Motion |
| State | Zustand (Client) + TanStack Query (Server) |
| Icons | Lucide React |

## Project Structure

```
safeclaw-ui/my-app/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── globals.css      # Global styles + CSS variables
│   │   ├── layout.tsx       # Root layout with providers
│   │   ├── page.tsx         # Main chat page
│   │   └── api/             # API Routes
│   │       ├── chat/
│   │       │   └── stream/
│   │       │       └── route.ts   # POST /api/chat/stream
│   │       ├── sessions/
│   │       │   └── route.ts       # GET/POST/DELETE /api/sessions
│   │       └── skills/
│   │           └── route.ts       # GET/POST /api/skills
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── collapsible.tsx
│   │   │   └── dropdown-menu.tsx
│   │   ├── chat-layout.tsx    # Main 3-panel layout
│   │   ├── sidebar.tsx        # Left sidebar (sessions, skills)
│   │   ├── chat-header.tsx    # Chat header with model selector
│   │   ├── message-list.tsx   # Message rendering with animations
│   │   ├── chat-input.tsx     # Input with quick actions
│   │   ├── thinking-indicator.tsx  # Agent thinking UI
│   │   ├── right-panel.tsx    # Right panel (execution graph)
│   │   ├── skill-tree.tsx     # Skill tree component
│   │   └── query-provider.tsx # TanStack Query provider
│   ├── hooks/              # Custom React hooks
│   │   ├── use-chat-stream.ts  # SSE streaming chat hook
│   │   ├── use-skills.ts       # Skills data hook
│   │   └── use-sessions.ts     # Sessions CRUD hook
│   ├── stores/             # Zustand state stores
│   │   └── chat-store.ts   # Chat state management
│   ├── types/              # TypeScript types
│   │   └── index.ts        # Shared type definitions
│   └── lib/                # Utilities
│       └── utils.ts        # cn() helper
├── public/                 # Static assets
├── next.config.ts          # Next.js config
├── package.json            # Dependencies
└── tsconfig.json           # TypeScript config
```

## Features

### ✅ Implemented

1. **Three-Panel Layout**
   - Left: Sessions, Workspaces, Skill Tree
   - Center: Chat interface with streaming
   - Right: Execution graph, Skills used, Context

2. **Session Management**
   - Create new sessions
   - Switch between sessions
   - Session history with message counts
   - Zustand persistence

3. **Skill Tree**
   - Hierarchical skill display
   - Enable/disable individual skills
   - Enable/disable entire folders
   - Expand/collapse folders

4. **Chat Interface**
   - Streaming message display
   - User/assistant message bubbles
   - Auto-scroll to latest message
   - Message timestamps

5. **Thinking Indicator**
   - Multi-step reasoning visualization
   - Step progress animation
   - Duration tracking per step
   - Tool usage display

6. **Execution Graph**
   - Visual execution flow
   - Step status indicators
   - Duration tracking
   - Connection lines between steps

7. **Model Selector**
   - Dropdown model selection
   - Model icons

8. **Quick Actions**
   - Deep Research
   - Analyze Data
   - Create Report
   - Code
   - Add Context

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## API Endpoints

### `/api/chat/stream` (POST)
Streaming chat endpoint with Server-Sent Events (SSE).

**Request:**
```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "sessionId": "optional-session-id",
  "enabledSkills": ["web-search", "data-analyzer"],
  "model": "gemma-4b"
}
```

**Response (SSE):**
```
data: {"type": "thinking", "step": "reasoning", "status": "running"}
data: {"type": "content", "content": "Hello!", "delta": "Hello"}
data: {"type": "done", "sessionId": "xxx", "messageId": "xxx", "usage": {...}}
```

### `/api/skills` (GET)
Retrieve skill tree hierarchy.

**Query Parameters:**
- `flat=true` - Return flat list instead of tree

**Response:**
```json
{
  "tree": [...],
  "total": 56,
  "categories": 3,
  "builtin": 5,
  "private": 2,
  "linked": 2
}
```

### `/api/skills` (POST)
Toggle skill or folder enabled state.

**Request:**
```json
// Toggle skill
{"skillId": "web-search", "enabled": true}

// Toggle folder
{"folderId": "built_in", "enabled": false}
```

### `/api/sessions` (GET)
List all sessions with pagination.

**Query Parameters:**
- `limit` - Max results (default: 20)
- `offset` - Pagination offset (default: 0)

**Response:**
```json
{
  "sessions": [...],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

### `/api/sessions` (POST)
Create new session.

**Request:**
```json
{"title": "New Chat", "model": "gemma-4b"}
```

### `/api/sessions?id={id}` (DELETE)
Delete a session.

## React Hooks

### `useChatStream`
Hook for streaming chat with SSE.

```tsx
const { sendMessage, abort, isStreaming, streamingContent } = useChatStream({
  onThinking: (step, status, duration) => {...},
  onContent: (content, delta) => {...},
  onComplete: (data) => {...},
  onError: (error) => {...},
});

await sendMessage({
  messages: [{ role: "user", content: "Hello" }],
  sessionId: "xxx",
  enabledSkills: ["web-search"],
  model: "gemma-4b",
});
```

### `useSkills`
Hook for skill tree management with TanStack Query.

```tsx
const {
  skills,
  skillsSummary,
  isLoading,
  toggleSkill,
  toggleFolder,
  refetch,
} = useSkills();
```

### `useSessions`
Hook for session CRUD with TanStack Query.

```tsx
const {
  sessions,
  total,
  isLoading,
  createSession,
  deleteSession,
  refetch,
} = useSessions();
```

## Migration from Streamlit

This Next.js UI replaces the previous Streamlit implementation with:

| Aspect | Streamlit | Next.js |
|--------|-----------|---------|
| Layout | Limited | Full control with Tailwind |
| State | Session state | Zustand + localStorage |
| Animation | Basic | Framer Motion |
| Components | Pre-built | Custom shadcn/ui |
| Routing | None | App Router |
| SSR | None | Full SSR support |
| Streaming | Limited | Native streaming support |

## Backend Integration

The current implementation uses mock data. To connect to a real FastAPI backend, configure the proxy in `next.config.ts`:

```typescript
async rewrites() {
  return [
    {
      source: '/api/py/:path*',
      destination: 'http://localhost:8000/:path*',
    },
  ];
}
```

Or modify the API routes to proxy requests to your Python backend.

## Next Steps

1. **Connect to Python Backend**: Replace mock data in API routes with real FastAPI calls
2. **Authentication**: Add user auth with Clerk or NextAuth
3. **Database**: Replace in-memory sessions with Postgres/MongoDB
4. **Real-time**: Add WebSocket support for real-time collaboration
5. **Deployment**: Deploy to Vercel with environment variables

## License

MIT
