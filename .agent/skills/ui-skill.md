```markdown
# GPT-like Theme Implementation Guide (Agent Spec)

## 1. Goal

Build a UI closely resembling ChatGPT’s interface:

- Fixed left sidebar
- Central chat area
- Minimal top header
- Sticky bottom input bar
- Clean, content-focused layout with strong whitespace usage

Do not use any official branding assets.

---

## 2. Layout Architecture

### Layout rules

- Root container: `display: flex; height: 100vh`
- Sidebar: fixed width (260–300px)
- Main area: `flex: 1; display: flex; flex-direction: column`

---

## 3. Design Tokens

### Colors & Typography
Use as setting in file `index.css`

### Spacing system

Base unit: 4px

| Token | Value |
| ----- | ----- |
| xs    | 4px   |
| sm    | 8px   |
| md    | 12px  |
| lg    | 16px  |
| xl    | 24px  |
| 2xl   | 32px  |

---

## 4. Sidebar

### Behavior

* Fixed position on the left
* Independent scrolling
* Optional collapsible state

### Content sections

* New chat button
* Search chats
* Chat history list
* Workspace / project area

### Styling rules

```css
.sidebar-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.sidebar-item:hover {
  background: var(--bg-secondary);
}
```

---

## 5. Main Chat Area

### Structure

* Header (top bar)
* Scrollable message list
* Sticky input area

### Message layout rules

* User messages: right aligned
* Assistant messages: left aligned
* Max width: ~720px
* Proper line wrapping

```css
.message {
  max-width: 720px;
  padding: 12px 16px;
  border-radius: 12px;
}
```

---

## 6. Input Bar

### Features

* Multiline text input
* Auto-resize behavior
* Send button (icon-based)
* Optional voice input button

### Behavior rules

* Sticky at bottom
* Centered container
* Rounded pill-style design

```css
.input-container {
  position: sticky;
  bottom: 0;
  padding: 16px;
  background: var(--bg-primary);
}

.input-box {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 10px;
}
```

---

## 7. Message Rendering Rules

### Assistant messages

* Must support Markdown
* Code blocks with syntax highlighting
* Proper paragraph spacing

### Code blocks

* Dark background
* Rounded corners (8–12px)
* Copy button in top-right corner

---

## 8. Interaction Design

### Hover states

* Subtle background change or opacity shift

### Active states

* Accent border or light highlight

### Transitions

* 150–200ms ease-in-out only

---

## 9. Scroll Behavior

* Sidebar: independent scroll container
* Chat area: main scrollable region
* Input always visible

---

## 10. Responsive Behavior

### Desktop

* Sidebar always visible

### Mobile

* Sidebar becomes drawer
* Input remains fixed at bottom
* Reduced padding for compact layout

---

## 11. Accessibility Requirements

* Minimum AA contrast compliance
* Full keyboard navigation support:

  * Sidebar items
  * Input field
  * Buttons
* Visible focus indicators

---

## 12. Optional Enhancements

* Chat history grouping (by time/date)
* Streaming text animation
* Regenerate response button
* Message actions (copy, edit, delete)

---

## 13. Anti-patterns (DO NOT DO)

* No overly saturated colors
* No heavy borders
* No large shadows
* No blocky card-heavy layout
* No centered page-style layout

---

## 14. Expected Agent Output

Agent should generate:

* Clean UI code (prefer React)
* Tailwind CSS or CSS variables
* Modular components:

  * Sidebar
  * ChatWindow
  * MessageList
  * InputBox

---

## 15. Summary

Build a UI that:

* Matches ChatGPT structural layout
* Prioritizes readability and content flow
* Uses minimal, modern design principles
* Focuses on chat usability over decoration

```
```
