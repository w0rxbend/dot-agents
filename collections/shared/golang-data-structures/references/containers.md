# Container Packages and String Builders

## container/list — Doubly-Linked List

General-purpose doubly-linked list. Elements hold `any` values (no type safety).

### Time Complexity

| Operation | Complexity | Notes |
| --- | --- | --- |
| **Insert at front/back** | O(1) | `PushFront()`, `PushBack()` |
| **Remove front/back** | O(1) | `l.Remove(l.Front())`, `l.Remove(l.Back())` |
| **Insert at arbitrary position** | O(1) | Given element reference (`*Element`) |
| **Remove at arbitrary position** | O(1) | Given element reference |
| **Access by index** | O(n) | Must walk chain; no random access |
| **Search for value** | O(n) | Linear scan required |

### When to Use

- LRU caches (O(1) move-to-front)
- Ordered collections with frequent insertion/removal at arbitrary positions
- Stable iterators that survive insertions

### When NOT to Use

Slices beat linked lists for most uses due to cache locality. If you only append/remove at ends, use slice or deque. Also avoid if O(1) random access by index needed.

### Use Cases

- Undo/redo stacks with stable element references
- Sliding window algorithms with frequent add/remove at both ends

## container/heap — Priority Queue

Interface-based min-heap. Provide type implementing `heap.Interface` (embeds `sort.Interface` plus `Push`/`Pop`).

### Time Complexity

| Operation | Complexity | Notes |
| --- | --- | --- |
| **heap.Push** | O(log n) | Appends and bubbles up |
| **heap.Pop** | O(log n) | Removes root, moves last to root, bubbles down |
| **heap.Init** | O(n) | Builds heap from unsorted slice in linear time |
| **heap.Fix** | O(log n) | Re-heapifies after priority change |
| **Peek (access root)** | O(1) | Direct access to `pq[0]` |
| **Search for value** | O(n) | No indexed lookup; must scan all items |

### Space Complexity

O(n): stores all items in backing slice. Heap is array-based, not tree of pointers.

### Use Cases

- Task scheduling (dequeue highest-priority tasks)
- Dijkstra's algorithm (repeatedly pop minimum-distance node)
- Huffman coding (repeatedly pop two smallest frequencies)
- Event processing (process events in time order)
- A\* pathfinding (explore nodes with lowest f-cost)
- Load balancing (process requests from server with lowest load)

## container/ring — Circular Buffer

Fixed-size circular linked list. Use for rolling windows and round-robin scheduling.

```go
// Rolling average of last 5 values
r := ring.New(5)
for _, v := range values {
    r.Value = v
    r = r.Next()
}

sum := 0.0
r.Do(func(v any) {
    if v != nil {
        sum += v.(float64)
    }
})
avg := sum / float64(r.Len())
```

## bufio — Buffered I/O

`bufio` wraps `io.Reader` and `io.Writer` in internal buffer, cutting system call overhead for frequent small reads/writes. Use `NewReader()` / `NewWriter()` for default 4096-byte buffers, `NewReaderSize()` / `NewWriterSize()` for custom sizes.

**bufio.Reader & Writer:** Call `Flush()` explicitly on writers and check its error. Buffered data is not written until flush or full buffer. Ignoring flush error can silently lose data.

**bufio.Scanner:** Line-by-line reading with `scanner.Scan()` and `scanner.Text()`. Default max token size is 64 KB. Call `scanner.Buffer()` to raise it for larger lines.

## strings.Builder vs bytes.Buffer

**strings.Builder:** Optimized for building strings from parts. `String()` returns accumulated string without copying. `Reset()` discards buffer.

**bytes.Buffer:** Implements both `io.Reader` and `io.Writer`. Use for I/O, encoding/decoding, or when both read and write needed. `Reset()` reuses allocated memory.

**Choose Builder for string concatenation, Buffer for I/O or buffer reuse in pools.**
