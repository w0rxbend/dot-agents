# Revisions and Comments — XML details

Deep reference for `docx_revisions.py` and `docx_comments.py`. Read when
reasoning about raw WordprocessingML, extending scripts, or debugging
unusual document. Everyday use needs only SKILL.md.

## Tracked changes (w:ins / w:del)

Word records run-level tracked changes as wrapper elements inside
paragraph (`w:p`), in `w` namespace
`http://schemas.openxmlformats.org/wordprocessingml/2006/main`:

```xml
<w:p>
  <w:r><w:t>Base </w:t></w:r>
  <w:ins w:id="1" w:author="Editor" w:date="2026-01-02T03:04:05Z">
    <w:r><w:t>inserted text</w:t></w:r>
  </w:ins>
  <w:del w:id="2" w:author="Editor" w:date="2026-01-02T03:04:05Z">
    <w:r><w:delText>deleted text</w:delText></w:r>
  </w:del>
</w:p>
```

Key facts script relies on:

- Deleted text lives in `w:delText`, not `w:t`. So plain text extraction
  naturally shows "accepted" view (insertions visible, deletions hidden).
- Resolution semantics:
  - accept `w:ins` → unwrap (move child runs up, drop wrapper)
  - reject `w:ins` → remove wrapper and its contents
  - accept `w:del` → remove wrapper and its contents
  - reject `w:del` → rename each `w:delText` to `w:t`, then unwrap
- Revisions can appear anywhere block content is allowed: body, table
  cells (nested tables too), headers, footers, text boxes. Script
  iterates body root plus every header/footer part root with
  `root.iter(W+"ins", W+"del")`, which finds them at any depth.
- `w:id` values are unique per revision *element*, but one logical edit
  session may produce several elements. `accept`/`reject --id` acts on
  exactly the element(s) carrying that id.

Not handled by script (detected by `docx_read.py --revisions` but left
alone): paragraph-mark revisions (`w:rPr/w:ins` on `w:pPr`), table row
insertions/deletions (`w:trPr/w:ins`), format-change records
(`w:rPrChange`, `w:pPrChange`), and moves (`w:moveFrom`/`w:moveTo`).
Moves are rare from typical editors. If present, handle file in Word
itself; do not guess.

## Comments

Three cooperating pieces:

1. **`word/comments.xml`** — one `w:comment` element per comment,
   carrying `w:id`, `w:author`, `w:initials`, `w:date`, and body
   paragraphs. Related from document.xml via relationship type
   `.../comments` and content type
   `application/vnd...wordprocessingml.comments+xml`. Also needs
   `[Content_Types].xml` override; python-docx's part machinery adds it
   when part is registered.
2. **Range markers in the story** — `w:commentRangeStart w:id="N"`
   before anchored runs, `w:commentRangeEnd w:id="N"` after them.
3. **The reference run** — `w:r` containing `w:commentReference
   w:id="N"`, placed right after range end. Ties balloon to location.

`docx_comments.py` behavior:

- **list / delete** always work at XML level, so they handle files from
  any producer. `anchored_text` is reconstructed by walking each part
  root in document order and collecting `w:t` text between start and
  end markers for each id.
- **add** first isolates target text into whole runs. If match starts
  or ends mid-run, run is split at boundary (split copies `w:rPr`, so
  formatting preserved). Then:
  - python-docx >= 1.2: native `document.add_comment(runs, ...)` API
    used (creates comments part, markers, and reference run itself).
  - older versions or `--xml`: script builds `word/comments.xml`,
    registers part + relationship through opc layer, and inserts
    markers/reference manually.
- Deleting comment removes `w:comment` element and all three marker
  kinds for that id. Anchored document text untouched.

Modern Word also writes `commentsExtended.xml` (threading/resolved
state). Scripts neither read nor produce it: replies and "resolved"
flags invisible here. Comments added by this skill are plain top-level
comments.
