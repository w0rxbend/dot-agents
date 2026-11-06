# AI Chat Library Guide

## Table of Contents

- [Vercel AI SDK](#vercel-ai-sdk)
- [Streamdown](#streamdown)
- [React Integration](#react-integration)
- [Alternative Libraries](#alternative-libraries)
- [Framework-Specific Solutions](#framework-specific-solutions)
- [Production Deployment](#production-deployment)

## Vercel AI SDK

Examples here target AI SDK 5 and later (`ai@5`+ with `@ai-sdk/react@2`+). Type-checked against `ai` 5.0 and 7.0. AI SDK 4 code (`useChat` from `ai/react`, `input`/`handleInputChange`/`handleSubmit`, `isLoading`, `message.content`, `toDataStreamResponse`) does not compile against these versions. If upgrading, see AI SDK migration guides.

### Installation & Setup

```bash
# Core packages
npm install ai @ai-sdk/react zod

# One provider package per model vendor you use
npm install @ai-sdk/openai      # OpenAI
npm install @ai-sdk/anthropic   # Anthropic
npm install @ai-sdk/google      # Google
```

Pick model ID from provider's current model list. Pass it through configuration (for example `CHAT_MODEL` environment variable), not hardcoded in components.

### Basic Implementation

```tsx
// app/api/chat/route.ts (Next.js App Router)
import { streamText, convertToModelMessages, type UIMessage } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: openai(process.env.CHAT_MODEL!),
    system: 'You are a helpful AI assistant.',
    messages: await convertToModelMessages(messages), // UI messages -> model messages
    maxOutputTokens: 2000,
  });

  return result.toUIMessageStreamResponse();
}
```

```tsx
// app/chat/page.tsx (Client Component)
'use client';

import { useState } from 'react';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { Streamdown } from 'streamdown';

export default function ChatPage() {
  const { messages, sendMessage, status, error, regenerate, stop } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }), // '/api/chat' is the default
    onFinish: ({ message }) => console.log('Message complete:', message.id),
    onError: err => console.error('Chat error:', err),
  });
  const [input, setInput] = useState('');
  const busy = status === 'submitted' || status === 'streaming';

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map(m => (
          <div key={m.id} className={`message ${m.role}`}>
            <div className="role">{m.role}</div>
            {m.parts.map((part, i) =>
              part.type === 'text' ? <Streamdown key={i}>{part.text}</Streamdown> : null
            )}
          </div>
        ))}
      </div>

      {error && (
        <div className="error" role="alert">
          Something went wrong.
          <button onClick={() => regenerate()}>Retry</button>
        </div>
      )}

      <form
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
          placeholder="Say something..."
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

Key differences from AI SDK 4: hook no longer manages input field, so keep it in own state. Send with `sendMessage({ text })`. Loading is `status` (`'submitted' | 'streaming' | 'ready' | 'error'`). Retry is `regenerate()`. Message content lives in `message.parts` (text, file, reasoning, tool parts), not `message.content`.

### Advanced Features

#### Tool Calling

```tsx
// app/api/chat/route.ts
import { streamText, convertToModelMessages, tool, stepCountIs, type UIMessage } from 'ai';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: openai(process.env.CHAT_MODEL!),
    messages: await convertToModelMessages(messages),
    tools: {
      weather: tool({
        description: 'Get current weather for a location',
        inputSchema: z.object({
          location: z.string().describe('City name'),
          unit: z.enum(['celsius', 'fahrenheit']).optional(),
        }),
        execute: async ({ location, unit = 'celsius' }) => fetchWeather(location, unit),
      }),
    },
    stopWhen: stepCountIs(5), // allow the model to call tools, then answer
  });

  return result.toUIMessageStreamResponse();
}
```

Declare tools with `inputSchema` (AI SDK 4 used `parameters`). Never evaluate model-provided expressions with `eval`. Use real parser or sandbox.

On client, tool call arrives as part named `tool-<toolName>` with `state`:

```tsx
{m.parts.map((part, i) => {
  switch (part.type) {
    case 'text':
      return <Streamdown key={i}>{part.text}</Streamdown>;
    case 'tool-weather':
      return (
        <pre key={i}>
          {part.state === 'output-available'
            ? JSON.stringify(part.output, null, 2)
            : 'Checking weather...'}
        </pre>
      );
    default:
      return null;
  }
})}
```

#### Multi-Modal Input (Images and Files)

`sendMessage` accepts `FileList` (or `FileUIPart[]`) next to text. Files come back as `file` parts:

```tsx
const [files, setFiles] = useState<FileList | undefined>();

<form
  onSubmit={e => {
    e.preventDefault();
    sendMessage({ text: input, files });
    setInput('');
    setFiles(undefined);
  }}
>
  <input type="file" accept="image/*" multiple onChange={e => setFiles(e.target.files ?? undefined)} />
  ...
</form>

// Rendering
case 'file':
  return part.mediaType.startsWith('image/') ? (
    <img key={i} src={part.url} alt={part.filename ?? 'attachment'} />
  ) : null;
```

Model must support media type. Validate type and size on server too.

#### Usage and Metadata

```tsx
const result = streamText({
  model: openai(process.env.CHAT_MODEL!),
  messages: await convertToModelMessages(messages),
  onFinish: ({ usage, finishReason }) => {
    console.log('Tokens used:', usage, 'finish reason:', finishReason);
  },
});

// Attach metadata (for example token totals) to the streamed assistant message
return result.toUIMessageStreamResponse({
  messageMetadata: ({ part }) =>
    part.type === 'finish' ? { totalTokens: part.totalUsage.totalTokens } : undefined,
});
```

On client, value is available as `message.metadata`.

## Streamdown

### Installation

[Streamdown](https://github.com/vercel/streamdown) is drop-in `react-markdown` replacement built for streaming AI output. Tolerates unterminated markdown (open code fences, bold, tables) while tokens arrive. npm package is `streamdown`:

```bash
npm install streamdown
```

Follow Streamdown README for Tailwind/CSS setup its default styles need.

### Basic Usage

```tsx
import { Streamdown } from 'streamdown';

function StreamingMessage({ text }: { text: string }) {
  return <Streamdown>{text}</Streamdown>;
}
```

Streamdown accepts `components` prop to override element renderers (as in `react-markdown`). Ships code highlighting, math and Mermaid support. Prop names change between releases. Check installed version's README before configuring them. Renders through React, not by injecting HTML strings. Hardens links and images by default. If you convert markdown to HTML string yourself instead, sanitize that HTML output (see `../SKILL.md`, Security Considerations).

## React Integration

### Custom Hooks

```tsx
// useStreamingMessage hook
function useStreamingMessage(initialContent = '') {
  const [content, setContent] = useState(initialContent);
  const [isStreaming, setIsStreaming] = useState(false);
  const contentRef = useRef('');

  const startStreaming = useCallback(() => {
    setIsStreaming(true);
    contentRef.current = '';
    setContent('');
  }, []);

  const appendChunk = useCallback((chunk: string) => {
    contentRef.current += chunk;
    setContent(contentRef.current);
  }, []);

  const endStreaming = useCallback(() => {
    setIsStreaming(false);
  }, []);

  return {
    content,
    isStreaming,
    startStreaming,
    appendChunk,
    endStreaming
  };
}

// useConversation hook
function useConversation(conversationId?: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [context, setContext] = useState({ tokens: 0, maxTokens: 4000 });

  // Load conversation
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId).then(setMessages);
    }
  }, [conversationId]);

  // Auto-save
  useEffect(() => {
    const saveTimer = setTimeout(() => {
      if (messages.length > 0) {
        saveConversation(conversationId, messages);
      }
    }, 1000);

    return () => clearTimeout(saveTimer);
  }, [messages, conversationId]);

  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
    updateTokenCount(message);
  }, []);

  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setMessages(prev =>
      prev.map(msg => msg.id === id ? { ...msg, ...updates } : msg)
    );
  }, []);

  const deleteMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  return {
    messages,
    context,
    addMessage,
    updateMessage,
    deleteMessage,
    clearConversation: () => setMessages([])
  };
}
```

### Component Library

```tsx
// Message component library
const ChatComponents = {
  Message: ({ message, onAction }) => (
    <div className={`message ${message.role}`}>
      <Avatar role={message.role} />
      <div className="message-content">
        <Streamdown>{message.content}</Streamdown>
      </div>
      <MessageActions message={message} onAction={onAction} />
    </div>
  ),

  Input: ({ onSubmit, disabled, placeholder }) => {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    }, [value]);

    return (
      <form onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) {
          onSubmit(value);
          setValue('');
        }
      }}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSubmit(value);
              setValue('');
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
        />
        <button type="submit" disabled={disabled || !value.trim()}>
          Send
        </button>
      </form>
    );
  },

  Thread: ({ messages, currentBranch, onBranchSwitch }) => (
    <div className="thread">
      {messages.map((msg, i) => (
        <React.Fragment key={msg.id}>
          {msg.branches && msg.branches.length > 1 && (
            <BranchSelector
              branches={msg.branches}
              current={currentBranch}
              onSelect={onBranchSwitch}
            />
          )}
          <ChatComponents.Message message={msg} />
        </React.Fragment>
      ))}
    </div>
  )
};
```

## Alternative Libraries

### Other AI SDKs

```tsx
// OpenAI SDK (direct)
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

async function chat(messages: any[]) {
  const stream = await openai.chat.completions.create({
    model: process.env.OPENAI_MODEL!,
    messages,
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

// Anthropic SDK
import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

async function claudeChat(prompt: string) {
  const message = await anthropic.messages.create({
    model: process.env.ANTHROPIC_MODEL!,
    max_tokens: 1000,
    messages: [{ role: 'user', content: prompt }],
  });

  return message.content;
}

// LangChain
import { ChatOpenAI } from '@langchain/openai';
import { HumanMessage, SystemMessage } from '@langchain/core/messages';

const model = new ChatOpenAI({
  model: process.env.OPENAI_MODEL!,
  temperature: 0.7,
  streaming: true,
});

const response = await model.invoke([
  new SystemMessage('You are a helpful assistant'),
  new HumanMessage('Hello!')
]);
```

### Markdown Renderers

```tsx
// react-markdown (alternative to Streamdown)
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

function MarkdownRenderer({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              language={match[1]}
              style={dark}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          );
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
```

## Framework-Specific Solutions

### Next.js Integration

```tsx
// app/api/chat/route.ts (App Router)
import { openai } from '@ai-sdk/openai';
import { streamText, convertToModelMessages, type UIMessage } from 'ai';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  // Auth check (getSession / checkRateLimit are your app's own helpers)
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { messages }: { messages: UIMessage[] } = await req.json();

  // Rate limiting
  const rateLimitResult = await checkRateLimit(session.userId);
  if (!rateLimitResult.allowed) {
    return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429 });
  }

  const result = streamText({
    model: openai(process.env.CHAT_MODEL!),
    messages: await convertToModelMessages(messages),
    // Treat stored preferences as data, not instructions
    system: 'You are a helpful assistant.',
  });

  // Streaming errors surface on the client via useChat's `error`; mask details here
  return result.toUIMessageStreamResponse({
    onError: () => 'Something went wrong. Please try again.',
  });
}
```

### Vue.js Integration

`@ai-sdk/vue` (AI SDK 5+) exposes `Chat` class with same `sendMessage` / `status` / `parts` model as React hook:

```vue
<!-- ChatComponent.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue';
import { Chat } from '@ai-sdk/vue';

const chat = new Chat({});
const input = ref('');
const busy = computed(() => chat.status === 'submitted' || chat.status === 'streaming');

function send() {
  if (!input.value.trim()) return;
  chat.sendMessage({ text: input.value });
  input.value = '';
}
</script>

<template>
  <div class="chat">
    <div v-for="message in chat.messages" :key="message.id" :class="`message ${message.role}`">
      <template v-for="(part, i) in message.parts" :key="i">
        <!-- Text interpolation is escaped. If you render markdown to HTML for v-html,
             sanitize the generated HTML with DOMPurify first. -->
        <p v-if="part.type === 'text'">{{ part.text }}</p>
      </template>
    </div>

    <form @submit.prevent="send">
      <input v-model="input" :disabled="busy" placeholder="Type a message..." />
      <button type="submit" :disabled="busy">{{ busy ? 'Sending...' : 'Send' }}</button>
    </form>
  </div>
</template>
```

## Production Deployment

### Environment Setup

```bash
# .env.local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...

# Rate limiting
UPSTASH_REDIS_URL=...
UPSTASH_REDIS_TOKEN=...

# Database
DATABASE_URL=postgresql://...

# Auth
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=...
```

### Production Checklist

```tsx
// Production configuration
const productionConfig = {
  // Error boundaries
  errorHandling: {
    onError: (error) => {
      console.error('Chat error:', error);
      trackError(error);
      showUserFriendlyError();
    },
    retry: {
      maxAttempts: 3,
      backoff: 'exponential'
    }
  },

  // Rate limiting
  rateLimit: {
    requests: 100,
    window: '1h',
    byUser: true
  },

  // Security
  security: {
    sanitizeOutput: true,
    validateInput: true,
    maxMessageLength: 10000,
    allowedFileTypes: ['image/png', 'image/jpeg', 'application/pdf']
  },

  // Performance
  performance: {
    streamingChunkSize: 10,
    debounceMs: 50,
    virtualScrollThreshold: 100,
    lazyLoadImages: true
  },

  // Analytics
  analytics: {
    trackEvents: true,
    collectFeedback: true,
    monitorLatency: true
  }
};
```

## Best Practices Summary

1. **Use a maintained chat SDK** - e.g. Vercel AI SDK; pin its major version
2. **Optimize performance** - Memoization, debouncing, virtual scroll
3. **Add auth & rate limiting** - Protect API endpoints
4. **Monitor usage** - Track tokens, costs, performance
5. **Test across providers** - OpenAI, Anthropic, Google
6. **Implement feedback loops** - Collect user feedback
7. **Follow accessibility guidelines** - ARIA, keyboard support