---
name: building-ai-chat
description: Builds the frontend of AI chat interfaces - ChatGPT-style message lists, streaming markdown rendering, input with attachments, stop/regenerate controls, token-limit indicators, feedback buttons, tool-call visualization and AI-specific error states - with the Vercel AI SDK (v5+) and Streamdown. Use when writing the chat UI of an assistant or copilot; not for backend agent logic, orchestration or memory (see agent-memory-systems, context-engineering).
---

# AI Chat Interface Components

## Purpose

Code targets React with Vercel AI SDK 5 or later. UI patterns apply to other stacks too.

## When to Use

Use for:
- ChatGPT-style conversational interfaces
- UI for AI assistants, copilots, chatbots
- Streaming text responses with markdown
- Conversation context and token limits
- Multi-modal inputs (text, images, files, voice)
- AI-specific errors (hallucinations, refusals, limits)
- Feedback (thumbs, regeneration, editing)
- Conversation branching or threading
- Tool/function calling visualization

## Quick Start

Minimal AI chat (AI SDK 5+; type-checked against `ai` 5.0 and 7.0):

```tsx
'use client';
import { useState } from 'react';
import { useChat } from '@ai-sdk/react';
import { Streamdown } from 'streamdown';

export function MinimalAIChat() {
  const { messages, sendMessage, status, stop } = useChat(); // POSTs to /api/chat
  const [input, setInput] = useState('');
  const busy = status === 'submitted' || status === 'streaming';

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map(m => (
          <div key={m.id} className={`message ${m.role}`}>
            {m.parts.map((part, i) =>
              part.type === 'text' ? <Streamdown key={i}>{part.text}</Streamdown> : null
            )}
          </div>
        ))}
        {status === 'submitted' && <div className="thinking">AI is thinking...</div>}
      </div>

      <form
        className="input-form"
        onSubmit={e => {
          e.preventDefault();
          if (!input.trim()) return;
          sendMessage({ text: input });
          setInput('');
        }}
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask anything..."
          disabled={busy}
        />
        {busy ? (
          <button type="button" onClick={() => stop()}>Stop</button>
        ) : (
          <button type="submit">Send</button>
        )}
      </form>
    </div>
  );
}
```

Matching server route (Next.js App Router):

```ts
// app/api/chat/route.ts
import { streamText, convertToModelMessages, type UIMessage } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: openai(process.env.CHAT_MODEL!), // choose a current model ID in config
    messages: await convertToModelMessages(messages),
  });
  return result.toUIMessageStreamResponse();
}
```

AI SDK 4 code (`ai/react`, `input`/`handleSubmit`, `isLoading`, `message.content`) does not compile against v5+. Fuller implementation: `examples/basic-chat.tsx`. Tools, files and metadata: `references/library-guide.md`.

## Core Components

### Message Display

```tsx
// Text of a UIMessage (AI SDK 5+) lives in message.parts
const text = message.parts.map(p => (p.type === 'text' ? p.text : '')).join('');

// User message
<div className="message user">
  <div className="content">{text}</div>
</div>

// AI message with streaming
<div className="message ai">
  <Streamdown className="content">{text}</Streamdown>
  {isStreaming && <span className="cursor">▊</span>}
</div>

// System message
<div className="message system">
  <Icon type="info" />
  <span>{text}</span>
</div>
```

Markdown rendering, code blocks, formatting: `references/message-components.md`.

### Input Components

```tsx
<div className="input-container">
  <button onClick={attachFile} aria-label="Attach file">
    <PaperclipIcon />
  </button>

  <textarea
    value={input}
    onChange={handleChange}
    onKeyDown={handleKeyDown}
    placeholder="Type a message..."
    rows={1}
    style={{ height: textareaHeight }}
  />

  <button onClick={toggleVoice} aria-label="Voice input">
    <MicIcon />
  </button>

  <button type="submit" disabled={!input.trim() || busy}>
    <SendIcon />
  </button>
</div>
```

### Response Controls

```tsx
<div className="response-controls">
  {isStreaming && (
    <button onClick={stop} className="stop-btn">
      Stop generating
    </button>
  )}

  {!isStreaming && (
    <>
      <button onClick={regenerate} aria-label="Regenerate response">
        <RefreshIcon /> Regenerate
      </button>
      <button onClick={continueGeneration} aria-label="Continue">
        Continue
      </button>
      <button onClick={editMessage} aria-label="Edit message">
        <EditIcon /> Edit
      </button>
    </>
  )}
</div>
```

### Feedback Mechanisms

```tsx
<div className="feedback-controls">
  <button
    onClick={() => sendFeedback('positive')}
    aria-label="Good response"
    className={feedback === 'positive' ? 'selected' : ''}
  >
    <ThumbsUpIcon />
  </button>

  <button
    onClick={() => sendFeedback('negative')}
    aria-label="Bad response"
    className={feedback === 'negative' ? 'selected' : ''}
  >
    <ThumbsDownIcon />
  </button>

  <button onClick={copyToClipboard} aria-label="Copy">
    <CopyIcon />
  </button>

  <button onClick={share} aria-label="Share">
    <ShareIcon />
  </button>
</div>
```

## Streaming & Real-Time UX

```tsx
// Use Streamdown for AI streaming (handles incomplete markdown)
import { Streamdown } from 'streamdown';

// Auto-scroll management
useEffect(() => {
  if (shouldAutoScroll()) {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }
}, [messages]);

// Smart auto-scroll heuristic
function shouldAutoScroll() {
  const threshold = 100; // px from bottom
  const isNearBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  const userNotReading = !hasUserScrolledUp && !isTextSelected;
  return isNearBottom && userNotReading;
}
```

Full streaming patterns, auto-scroll behavior, stop generation: `references/streaming-patterns.md`.

## Context Management

```tsx
// User-friendly token display
function TokenIndicator({ used, total }) {
  const percentage = (used / total) * 100;
  const remaining = total - used;

  return (
    <div className="token-indicator">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
      <span className="token-text">
        {percentage > 80
          ? `⚠️ About ${Math.floor(remaining / 250)} messages left`
          : `${Math.floor(remaining / 250)} pages of conversation remaining`}
      </span>
    </div>
  );
}
```

Summarization strategies, conversation branching, organization: `references/context-management.md`.

## Multi-Modal Support

```tsx
// Image upload with preview
function ImageUpload({ onUpload }) {
  return (
    <div
      className="upload-zone"
      onDrop={handleDrop}
      onDragOver={preventDefault}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        multiple
        hidden
        ref={fileInputRef}
      />
      {previews.map(preview => (
        <img key={preview.id} src={preview.url} alt="Upload preview" />
      ))}
    </div>
  );
}
```

Full multi-modal patterns, including voice and screen sharing: `references/multimodal-input.md`.

## Error Handling

```tsx
// Refusal handling
if (response.type === 'refusal') {
  return (
    <div className="error refusal">
      <Icon type="info" />
      <p>I cannot help with that request.</p>
      <details>
        <summary>Why?</summary>
        <p>{response.reason}</p>
      </details>
      <p>Try asking: {response.suggestion}</p>
    </div>
  );
}

// Rate limit communication
if (error.code === 'RATE_LIMIT') {
  return (
    <div className="error rate-limit">
      <p>Please wait {error.retryAfter} seconds</p>
      <CountdownTimer seconds={error.retryAfter} onComplete={retry} />
    </div>
  );
}
```

All error patterns: `references/error-handling.md`.

## Tool Usage Visualization

```tsx
function ToolUsage({ tool }) {
  return (
    <div className="tool-usage">
      <div className="tool-header">
        <Icon type={tool.type} />
        <span>{tool.name}</span>
        {tool.status === 'running' && <Spinner />}
      </div>
      {tool.status === 'complete' && (
        <details>
          <summary>View details</summary>
          <pre>{JSON.stringify(tool.result, null, 2)}</pre>
        </details>
      )}
    </div>
  );
}
```

Function calling, code execution, web search patterns: `references/tool-usage.md`.

## Implementation Guide

### Recommended Stack

Primary libraries (AI SDK 5 or later; current majors at time of writing: `ai` 7, `streamdown` 2):

```bash
# Core AI chat functionality (plus one provider package)
npm install ai @ai-sdk/react @ai-sdk/openai

# Streaming markdown rendering (package name is `streamdown`)
npm install streamdown

# Only if you convert markdown to HTML strings yourself
npm install dompurify marked
```

### Performance Optimization

```tsx
// Memoize message rendering
const MemoizedMessage = memo(Message, (prev, next) =>
  prev.content === next.content && prev.isStreaming === next.isStreaming
);

// Debounce streaming updates
const debouncedUpdate = useMemo(
  () => debounce(updateMessage, 50),
  []
);

// Virtual scrolling for long conversations
import { VariableSizeList } from 'react-window';
```

Performance details: `references/streaming-patterns.md` and `references/performance-optimization.md`.

### Security Considerations

Treat model output as untrusted. Sanitize where markdown becomes HTML, not before:

- Rendering through React (Streamdown, `react-markdown`) does not inject raw HTML strings. Streamdown also runs `rehype-sanitize` and `rehype-harden` (link/image hardening). Do not enable raw-HTML plugins for model output.
- DOMPurify on markdown source does not protect you, because markdown renderer runs afterwards. It also mangles code blocks containing `<`.
- If you render markdown to HTML string yourself (for `dangerouslySetInnerHTML` or `v-html`), sanitize generated HTML:

```tsx
import DOMPurify from 'dompurify';
import { marked } from 'marked';

function SafeMarkdown({ markdown }: { markdown: string }) {
  const html = DOMPurify.sanitize(marked.parse(markdown, { async: false }) as string);
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />;
}
```

### Accessibility

```tsx
// ARIA live regions for screen readers
<div role="log" aria-live="polite" aria-relevant="additions">
  {messages.map(msg => (
    <article key={msg.id} role="article" aria-label={`${msg.role} message`}>
      {msg.parts.map((p, i) => (p.type === 'text' ? <p key={i}>{p.text}</p> : null))}
    </article>
  ))}
</div>

// Loading announcements
<div role="status" aria-live="polite" className="sr-only">
  {status === 'streaming' ? 'AI is responding' : ''}
</div>
```

Full accessibility patterns: `references/accessibility-chat.md`.

## Bundled Resources

### Scripts (Token-Free Execution)

- Run `scripts/parse_stream.js` to parse incomplete markdown during streaming
- Run `scripts/calculate_tokens.py` to estimate token usage and context limits
- Run `scripts/format_messages.js` to format message history for export

### References (Progressive Disclosure)

- `references/streaming-patterns.md` - Streaming UX, auto-scroll, stop/regenerate, render performance
- `references/context-management.md` - Token limits and conversation strategies
- `references/multimodal-input.md` - Image, file, voice handling
- `references/feedback-loops.md` - User feedback and RLHF patterns
- `references/error-handling.md` - AI-specific error scenarios
- `references/tool-usage.md` - Visualizing function calls and tool use
- `references/accessibility-chat.md` - Screen reader, keyboard, contrast, mobile support
- `references/library-guide.md` - AI SDK 5+ and Streamdown setup, tools, files, metadata
- `references/performance-optimization.md` - Streaming performance patterns

### Examples

- `examples/basic-chat.tsx` - Minimal ChatGPT-style interface
- `examples/streaming-chat.tsx` - Advanced streaming with memoization
- `examples/multimodal-chat.tsx` - Images and file uploads
- `examples/code-assistant.tsx` - IDE-style code copilot
- `examples/tool-calling-chat.tsx` - Function calling visualization

### Assets

- `assets/system-prompts.json` - Curated prompts per use case
- `assets/message-templates.json` - Pre-built message components
- `assets/error-messages.json` - User-friendly error messages
- `assets/themes.json` - Light, dark, high-contrast themes

## Design Token Integration

Style chat components with design tokens (CSS custom properties) to follow app theme:

```css
/* Message bubbles use design tokens */
.message.user {
  background: var(--message-user-bg, var(--color-primary));
  color: var(--message-user-text, var(--color-white));
  padding: var(--message-padding, var(--spacing-md));
  border-radius: var(--message-border-radius, var(--radius-lg));
}

.message.ai {
  background: var(--message-ai-bg, var(--color-gray-100));
  color: var(--message-ai-text, var(--color-text-primary));
}
```

Token system, light/dark and high-contrast themes: use theming-components skill.
