# Frontend Architecture Guide
## Core Principles
### 1. Break UI into small focused components
Mỗi component chỉ nên có **một trách nhiệm UI rõ ràng**.

Không tạo component khổng lồ kiểu:
```text id="4o4vvh"
ChatPage.tsx
```

dài 1000 dòng chứa:
* fetch data
* rendering
* modal
* sidebar
* input
* business logic
* animation
* state

Thay vào đó
```text id="4g1c3v"
ChatPage
 ├── ChatLayout
 ├── MessageList
 │    ├── UserMessage
 │    └── AssistantMessage
 ├── ChatInput
 ├── PipelineSidebar
 └── SourcePanel
```

---

# Component Responsibilities

## Presentational Components

Ưu tiên viết component dạng:

```text id="d0s12x"
data in
UI out
```
Ví dụ:

```tsx id="j00z5g"
type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
};

export function MessageBubble({
  role,
  content,
}: MessageBubbleProps) {
  return (
    <div>
      {content}
    </div>
  );
}
```

Component này:
* không fetch
* không biết API
* không biết global state
* không mutate app state

---

# State Ownership Rules

## Local state stays local

Nếu state chỉ phục vụ UI nội bộ component:
→ component tự quản lý bằng:
```tsx id="ynm2cq"
useState
```

Ví dụ:

* accordion open/close
* dropdown visibility
* hover state
* input focus
* tab selection nội bộ
* modal open state chỉ dùng nội bộ

Ví dụ:

```tsx id="h0tb9r"
const [isExpanded, setIsExpanded] = useState(false);
```

Không lift state unnecessarily.

---

# Shared state should be lifted

Chỉ đưa state lên parent/global khi:

* nhiều component cùng dùng
* cần synchronize
* cần persist
* cần server interaction
* cần cross-page access

Ví dụ:

* current chat session
* authenticated user
* streamed messages
* pipeline execution state

---

# Avoid Prop Drilling Hell

Nếu prop truyền qua quá nhiều layer:

```text id="smd6ql"
Page
 -> Layout
   -> SidebarWrapper
     -> Sidebar
```

thì dùng:

* context
* store
* feature state

Nhưng:

* không globalize mọi thứ
* không dùng store cho UI toggle nhỏ

---

# Smart vs Dumb Components

## Smart Components

Chứa:

* API calls
* orchestration
* shared state
* business logic

Ví dụ:

```text id="jz2k0l"
ChatPage
ChatContainer
PipelineController
```

---

## Dumb Components

Chỉ render UI.

Ví dụ:

```text id="3q4mxs"
MessageBubble
SourceCard
PipelineStep
TypingIndicator
```

---

# Data Flow

Ưu tiên:

```text id="x5dwb5"
top-down data flow
```

```text id="3u5g8y"
Parent owns shared state
→ passes data via props
→ child emits events via callbacks
```

Ví dụ:

```tsx id="esxj2z"
<MessageInput
  onSend={handleSend}
/>
```

Không để child mutate random global state trực tiếp nếu không cần.

---

# Component File Structure

Ưu tiên:

```text id="sq0m5z"
components/
  chat/
    ChatInput.tsx
    MessageList.tsx
    MessageBubble.tsx

  pipeline/
    PipelineSidebar.tsx
    PipelineStepCard.tsx
```

Không dump toàn bộ vào:

```text id="lnp6kc"
components/
```

---

# Business Logic Separation

Không nhét business logic lớn vào JSX.

Sai:

```tsx id="9u5cl8"
return (
  messages.filter(...).map(...)
)
```

nếu logic dài/phức tạp.

Tách:

```tsx id="m8gmx8"
const visibleMessages = getVisibleMessages(messages);
```

hoặc custom hook:

```tsx id="eqqg6v"
const {
  messages,
  sendMessage,
} = useChat();
```

---

# Custom Hooks

Dùng hook cho:

* reusable logic
* API orchestration
* subscriptions
* streaming
* websocket/SSE
* form handling

Ví dụ:

```text id="hsv5zq"
useChat
usePipelineTrace
useSSEStream
```

---

# Avoid Massive Global Stores

Không biến:

* Zustand
* Redux
* Context

thành garbage dump.

Global state chỉ nên chứa:

* app-wide state
* cross-feature state
* persisted session state

Không store:

* hover
* accordion open
* temporary modal UI

---

# Component Reusability

Component nên:

* composable
* configurable bằng props
* không hardcode business context

Tốt:

```tsx id="nsy12t"
<DataTable
  columns={columns}
  data={rows}
/>
```

Kém:

```tsx id="4sm9oq"
<UserManagementTable />
```

nếu logic/table structure generic.

---

# UI Components vs Feature Components

## UI Components

Generic reusable:

```text id="7gwxsd"
Button
Modal
Tabs
Card
```

---

## Feature Components

Business/domain-specific:

```text id="n6ikbi"
ChatSidebar
PipelineTracePanel
KGNodeInspector
```

---

# Side Effects

Không gọi:

* fetch
* websocket
* SSE
* timers

trực tiếp lung tung trong render logic.

Đặt trong:

```tsx id="11en8g"
useEffect
```

hoặc custom hook.

---

# Recommended Mental Model

## Components should ideally:

### Receive:

* props
* callbacks
* local UI state only if internal

### Avoid:

* hidden dependencies
* random global mutations
* fetching everywhere
* giant multi-purpose components

---

# Architecture Goal

Mục tiêu là đạt được:

```text id="6r4p0j"
easy to:
- debug
- reuse
- test
- replace
- scale
- reason about
```

chứ không phải:

```text id="a7j4t5"
minimum number of files
```

File ít nhưng coupling cao thường bảo trì tệ hơn rất nhiều.
