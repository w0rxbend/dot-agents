# Offline Sync Reference Guide

## Table of Contents

- [The Offline Challenge](#the-offline-challenge)
- [Architecture Pattern](#architecture-pattern)
- [Yjs + IndexedDB Pattern](#yjs-indexeddb-pattern)
  - [Setup](#setup)
  - [Workflow](#workflow)
- [Connection Status Indicator](#connection-status-indicator)
- [Pending Changes Counter](#pending-changes-counter)
- [Manual Sync Trigger](#manual-sync-trigger)
- [Conflict Resolution](#conflict-resolution)
- [Last Sync Timestamp](#last-sync-timestamp)
- [Data Reconciliation](#data-reconciliation)
- [Retry Strategy](#retry-strategy)
- [Mobile-Specific Patterns](#mobile-specific-patterns)
  - [Background Sync (Service Worker)](#background-sync-service-worker)
  - [Low Battery Mode](#low-battery-mode)
  - [Data Saver Mode](#data-saver-mode)
- [Storage Quota Management](#storage-quota-management)
- [Clear Old Data](#clear-old-data)
- [Testing Offline Scenarios](#testing-offline-scenarios)
  - [Simulate Offline Mode](#simulate-offline-mode)
  - [Simulate Flaky Connection](#simulate-flaky-connection)

## The Offline Challenge

**Requirements:**
- Queue mutations locally
- Apply optimistically to UI (instant feedback)
- Sync on reconnect
- Resolve conflicts automatically
- No data loss

## Architecture Pattern

```
┌────────────────────────────────────────────────────────┐
│              Offline-First Architecture                 │
├────────────────────────────────────────────────────────┤
│                                                         │
│  User Action (edit, move, delete)                      │
│         ↓                                               │
│  ┌──────────────────────────┐                          │
│  │  Local CRDT Update       │                          │
│  │  (Yjs Y.Doc)             │                          │
│  └──────────┬───────────────┘                          │
│             ├─── Apply to UI (optimistic)              │
│             ↓                                           │
│  ┌──────────────────────────┐                          │
│  │  Local Storage Queue     │                          │
│  │  (IndexedDB)             │                          │
│  └──────────┬───────────────┘                          │
│             │                                           │
│             ↓                                           │
│  Connection status check                                │
│  ├─ OFFLINE: Store locally                             │
│  └─ ONLINE: Sync to server                             │
│                                                         │
│  ┌──────────────────────────┐                          │
│  │  WebSocket/HTTP Sync     │                          │
│  └──────────┬───────────────┘                          │
│             ↓                                           │
│  Backend CRDT merge (conflict-free)                     │
│  Broadcast to other clients                             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

## Yjs + IndexedDB Pattern

Yjs with IndexedDB gives automatic offline support.

### Setup

```typescript
import * as Y from 'yjs'
import { IndexeddbPersistence } from 'y-indexeddb'
import { WebsocketProvider } from 'y-websocket'

const doc = new Y.Doc()

// 1. Local persistence (loads immediately)
const indexeddbProvider = new IndexeddbPersistence('my-document', doc)

indexeddbProvider.on('synced', () => {
  console.log('✅ Loaded from IndexedDB')
})

// 2. Server sync (connects in background)
const wsProvider = new WebsocketProvider(
  'wss://api.example.com/sync',
  'my-document',
  doc,
  { connect: true }
)

wsProvider.on('status', (event) => {
  if (event.status === 'connected') {
    console.log('✅ Online - syncing to server...')
  } else {
    console.log('📴 Offline - queuing locally...')
  }
})

wsProvider.on('sync', (isSynced) => {
  if (isSynced) {
    console.log('✅ Fully synced with server')
  }
})

// All changes automatically:
// 1. Applied to IndexedDB (instant)
// 2. Queued for server sync
// 3. Synced when online
// 4. Merged conflict-free
```

### Workflow

```
1. Page Load
   ↓
   Load from IndexedDB (instant, last known state)
   ↓
   Display UI (user can start working immediately)
   ↓
   Connect to server in background
   ↓
   Sync differences (CRDTs merge conflict-free)
   ↓
   UI updates if server had newer changes

2. User Makes Changes (Offline)
   ↓
   Apply to local CRDT (Y.Doc)
   ↓
   Save to IndexedDB (automatic)
   ↓
   Update UI (optimistic)
   ↓
   Queue for server sync (automatic)

3. Connection Restored
   ↓
   WebSocket reconnects (automatic exponential backoff)
   ↓
   Send queued changes to server
   ↓
   Receive changes from server
   ↓
   CRDT merge (conflict-free)
   ↓
   UI updates if needed
```

## Connection Status Indicator

Show online/offline/syncing status to user.

```typescript
import { WebsocketProvider } from 'y-websocket'

type ConnectionStatus = 'online' | 'offline' | 'syncing' | 'error'

function setupConnectionMonitor(provider: WebsocketProvider) {
  let status: ConnectionStatus = 'offline'

  const updateStatusUI = (newStatus: ConnectionStatus) => {
    status = newStatus

    const indicator = document.getElementById('connection-status')
    if (!indicator) return

    indicator.className = `status-${status}`

    const messages = {
      online: '✅ Online',
      offline: '📴 Offline',
      syncing: '🔄 Syncing...',
      error: '⚠️ Connection error'
    }

    indicator.textContent = messages[status]
  }

  provider.on('status', (event: { status: string }) => {
    if (event.status === 'connected') {
      updateStatusUI('syncing')
    } else {
      updateStatusUI('offline')
    }
  })

  provider.on('sync', (isSynced: boolean) => {
    if (isSynced) {
      updateStatusUI('online')
    }
  })

  // Network status (browser API)
  window.addEventListener('online', () => {
    console.log('Network: online')
    updateStatusUI('syncing')
  })

  window.addEventListener('offline', () => {
    console.log('Network: offline')
    updateStatusUI('offline')
  })

  // Initial state
  if (navigator.onLine) {
    updateStatusUI('syncing')
  } else {
    updateStatusUI('offline')
  }
}
```

**CSS:**
```css
.status-online {
  background: #00cc00;
  color: white;
}

.status-offline {
  background: #666;
  color: white;
}

.status-syncing {
  background: #ff9900;
  color: white;
}

.status-error {
  background: #cc0000;
  color: white;
}
```

## Pending Changes Counter

Show count of unsynced changes.

```typescript
function setupPendingChangesMonitor(
  doc: Y.Doc,
  provider: WebsocketProvider
) {
  let pendingChanges = 0
  let isOnline = false

  provider.on('status', (event) => {
    isOnline = event.status === 'connected'
    updateUI()
  })

  provider.on('sync', (isSynced) => {
    if (isSynced) {
      pendingChanges = 0
      updateUI()
    }
  })

  doc.on('update', (update) => {
    if (!isOnline) {
      pendingChanges++
      updateUI()
    }
  })

  function updateUI() {
    const badge = document.getElementById('pending-changes-badge')
    if (!badge) return

    if (pendingChanges > 0) {
      badge.textContent = `${pendingChanges} pending`
      badge.style.display = 'block'
    } else {
      badge.style.display = 'none'
    }
  }
}
```

## Manual Sync Trigger

Let users trigger sync manually.

```typescript
function setupManualSync(provider: WebsocketProvider) {
  const syncButton = document.getElementById('sync-button')

  if (syncButton) {
    syncButton.addEventListener('click', async () => {
      syncButton.textContent = 'Syncing...'
      syncButton.disabled = true

      try {
        // Disconnect and reconnect to force sync
        provider.disconnect()
        await new Promise(resolve => setTimeout(resolve, 100))
        provider.connect()

        // Wait for sync
        await new Promise<void>((resolve) => {
          provider.on('sync', (isSynced) => {
            if (isSynced) resolve()
          })
        })

        syncButton.textContent = '✓ Synced'
      } catch (error) {
        syncButton.textContent = '✗ Sync failed'
        console.error('Sync error:', error)
      } finally {
        setTimeout(() => {
          syncButton.textContent = 'Sync'
          syncButton.disabled = false
        }, 2000)
      }
    })
  }
}
```

## Conflict Resolution

CRDTs resolve conflicts automatically. Merges can still be detected:

```typescript
doc.on('update', (update, origin, doc, transaction) => {
  // Check if update came from remote
  if (origin !== doc) {
    console.log('Received remote update - merged automatically')

    // Optionally notify user
    const changes = transaction.changed

    if (changes.size > 0) {
      showNotification('Document updated by another user')
    }
  }
})
```

## Last Sync Timestamp

Track when document last synced with server.

```typescript
let lastSyncTime: number | null = null

provider.on('sync', (isSynced) => {
  if (isSynced) {
    lastSyncTime = Date.now()

    // Store in localStorage
    localStorage.setItem(
      `last-sync-${documentId}`,
      lastSyncTime.toString()
    )

    updateLastSyncUI()
  }
})

function updateLastSyncUI() {
  const element = document.getElementById('last-sync-time')
  if (!element) return

  if (!lastSyncTime) {
    element.textContent = 'Never synced'
    return
  }

  const now = Date.now()
  const elapsed = now - lastSyncTime

  if (elapsed < 60000) {
    element.textContent = 'Just now'
  } else if (elapsed < 3600000) {
    element.textContent = `${Math.floor(elapsed / 60000)}m ago`
  } else if (elapsed < 86400000) {
    element.textContent = `${Math.floor(elapsed / 3600000)}h ago`
  } else {
    element.textContent = new Date(lastSyncTime).toLocaleDateString()
  }
}

// Update every minute
setInterval(updateLastSyncUI, 60000)
```

## Data Reconciliation

Use when local and server state diverge significantly.

```typescript
async function reconcileData(
  doc: Y.Doc,
  provider: WebsocketProvider
) {
  // Get current local state
  const localState = Y.encodeStateAsUpdate(doc)

  // Request full server state
  provider.disconnect()

  // Clear local doc
  const newDoc = new Y.Doc()

  // Load server state
  provider.doc = newDoc
  provider.connect()

  // Wait for sync
  await new Promise<void>((resolve) => {
    provider.on('sync', (isSynced) => {
      if (isSynced) resolve()
    })
  })

  // Apply local changes on top
  Y.applyUpdate(newDoc, localState)

  console.log('Reconciliation complete')
}
```

## Retry Strategy

Exponential backoff for failed syncs.

```typescript
class RetryableWebSocketProvider {
  private provider: WebsocketProvider
  private reconnectAttempts = 0
  private maxReconnectDelay = 30000  // 30 seconds
  private reconnectTimeout: NodeJS.Timeout | null = null

  constructor(url: string, roomName: string, doc: Y.Doc) {
    this.provider = new WebsocketProvider(url, roomName, doc, {
      connect: false  // Manual connection control
    })

    this.setupEventHandlers()
    this.connect()
  }

  private setupEventHandlers() {
    this.provider.on('status', (event) => {
      if (event.status === 'connected') {
        console.log('Connected to server')
        this.reconnectAttempts = 0  // Reset on successful connection
      } else {
        console.log('Disconnected from server')
        this.scheduleReconnect()
      }
    })
  }

  private connect() {
    console.log('Attempting connection...')
    this.provider.connect()
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    )

    // Add jitter (0-1000ms) to prevent thundering herd
    const jitter = Math.random() * 1000

    console.log(`Reconnecting in ${Math.floor((delay + jitter) / 1000)}s...`)

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay + jitter)
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }
    this.provider.disconnect()
  }
}
```

## Mobile-Specific Patterns

### Background Sync (Service Worker)

For PWAs, use Background Sync API to sync on reconnect.

```typescript
// Register service worker
if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
  navigator.serviceWorker.register('/sw.js')
}

// Request background sync when offline
async function requestBackgroundSync() {
  const registration = await navigator.serviceWorker.ready

  try {
    await registration.sync.register('yjs-sync')
    console.log('Background sync registered')
  } catch (error) {
    console.error('Background sync failed:', error)
  }
}

// In service worker (sw.js)
self.addEventListener('sync', (event) => {
  if (event.tag === 'yjs-sync') {
    event.waitUntil(syncYjsDocument())
  }
})

async function syncYjsDocument() {
  // Load document from IndexedDB
  // Sync to server
  // Return promise
}
```

### Low Battery Mode

Reduce sync frequency on low battery.

```typescript
function setupBatteryOptimization(provider: WebsocketProvider) {
  if ('getBattery' in navigator) {
    (navigator as any).getBattery().then((battery: any) => {
      const updateSyncFrequency = () => {
        if (battery.charging) {
          // Normal sync (real-time)
          provider.connect()
        } else if (battery.level < 0.2) {
          // Low battery - sync every 5 minutes
          provider.disconnect()
          setInterval(() => {
            provider.connect()
            setTimeout(() => provider.disconnect(), 10000)
          }, 5 * 60 * 1000)
        } else {
          // Normal sync
          provider.connect()
        }
      }

      battery.addEventListener('chargingchange', updateSyncFrequency)
      battery.addEventListener('levelchange', updateSyncFrequency)

      updateSyncFrequency()
    })
  }
}
```

### Data Saver Mode

Compress data on cellular connections.

```typescript
if ('connection' in navigator) {
  const connection = (navigator as any).connection

  connection.addEventListener('change', () => {
    const type = connection.effectiveType

    if (type === '4g' || connection.type === 'wifi') {
      // Normal sync frequency
      console.log('Fast connection - normal sync')
    } else if (type === '3g' || type === '2g') {
      // Reduce sync frequency
      console.log('Slow connection - reduced sync')
    }

    // Check if data saver is enabled
    if (connection.saveData) {
      console.log('Data saver enabled - minimal sync')
    }
  })
}
```

## Storage Quota Management

Monitor IndexedDB storage. Warn when space runs low.

```typescript
async function checkStorageQuota() {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    const estimate = await navigator.storage.estimate()

    const usage = estimate.usage || 0
    const quota = estimate.quota || 0
    const percentUsed = (usage / quota) * 100

    console.log(`Storage: ${Math.round(usage / 1024 / 1024)}MB / ${Math.round(quota / 1024 / 1024)}MB (${percentUsed.toFixed(1)}%)`)

    if (percentUsed > 80) {
      showWarning('Storage almost full - consider clearing old documents')
    }
  }
}

// Check on page load
checkStorageQuota()

// Check after large syncs
provider.on('sync', checkStorageQuota)
```

## Clear Old Data

Garbage-collect old documents.

```typescript
async function clearOldDocuments(maxAgeMs: number = 30 * 24 * 60 * 60 * 1000) {
  const db = await openIndexedDB()
  const transaction = db.transaction(['documents'], 'readwrite')
  const store = transaction.objectStore('documents')

  const request = store.openCursor()

  request.onsuccess = (event) => {
    const cursor = (event.target as IDBRequest).result

    if (cursor) {
      const doc = cursor.value
      const age = Date.now() - doc.lastModified

      if (age > maxAgeMs) {
        console.log(`Deleting old document: ${doc.id}`)
        cursor.delete()
      }

      cursor.continue()
    } else {
      console.log('Cleanup complete')
    }
  }
}

// Run cleanup weekly
setInterval(clearOldDocuments, 7 * 24 * 60 * 60 * 1000)
```

## Testing Offline Scenarios

### Simulate Offline Mode

```typescript
// Disconnect from server
provider.disconnect()

// Make changes
ytext.insert(0, 'This was written offline')

// Wait 5 seconds
await new Promise(resolve => setTimeout(resolve, 5000))

// Reconnect
provider.connect()

// Verify sync
await new Promise<void>((resolve) => {
  provider.on('sync', (isSynced) => {
    if (isSynced) {
      console.log('✅ Offline changes synced successfully')
      resolve()
    }
  })
})
```

### Simulate Flaky Connection

```typescript
// Randomly disconnect/reconnect
setInterval(() => {
  if (Math.random() > 0.5) {
    provider.disconnect()
    console.log('📴 Simulating connection loss')

    setTimeout(() => {
      provider.connect()
      console.log('✅ Simulating connection restored')
    }, Math.random() * 5000)
  }
}, 10000)
```
