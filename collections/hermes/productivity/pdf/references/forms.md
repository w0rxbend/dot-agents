# Building Fillable Forms: spec format and workflow

One JSON spec drives `pdf_form_layout.py` (design lint) and
`pdf_make_form.py` (AcroForm build). Coordinates are PDF points, origin at
page bottom-left (1 pt = 1/72 inch; A4 is 595.27 x 841.89, letter is
612 x 792).

## Spec shape

```json
{
  "title": "Example Intake Form",
  "author": "example-author",
  "page_size": "A4",
  "page_count": 1,
  "fields": [
    {"name": "surname", "type": "text", "page": 1,
     "label": "Surname", "label_box": [72, 700, 150, 714],
     "entry_box": [160, 696, 400, 716],
     "value": "", "tooltip": "Family name"},

    {"name": "agree", "type": "checkbox", "page": 1,
     "label": "I agree", "label_box": [72, 660, 150, 674],
     "entry_box": [160, 658, 176, 674], "checked": false},

    {"name": "color", "type": "radio", "page": 1,
     "label": "Color", "label_box": [72, 620, 150, 634],
     "entry_box": [160, 616, 400, 636],
     "options": ["red", "blue"], "value": "blue"},

    {"name": "size", "type": "dropdown", "page": 1,
     "label": "Size", "label_box": [72, 580, 150, 594],
     "entry_box": [160, 576, 300, 596],
     "options": ["small", "large"], "value": "small"}
  ]
}
```

- `page_size`: `"A4"`, `"letter"`, or `[width, height]` in points.
- `page_count`: optional; auto-extended to highest field page.
- Boxes are `[x0, y0, x1, y1]` with `x0 < x1`, `y0 < y1`.
- `label`: static text drawn near `label_box`. Omit it (and
  `label_box`) for unlabeled fields.
- `radio`: buttons laid left-to-right inside `entry_box`, one slot per
  option, each with small static caption. `value` pre-selects option by
  export name.
- `dropdown` maps to AcroForm choice (combo) field.

## Field types → what pdf_read.py --fields reports

| Spec type | /FT | value format after fill |
|---|---|---|
| text | /Tx (`text`) | string |
| checkbox | /Btn (`button`) | `/Yes` or `/Off` |
| radio | /Btn (`button`) | `/<export>`, e.g. `/red` |
| dropdown | /Ch (`choice`) | option string |

Filling with `pdf_fill_form.py`: checkboxes accept `true`/`false`; radio
values need leading slash (`"/red"`); dropdown values are plain option
string.

## Layout lint rules (pdf_form_layout.py)

Per field, on its declared page:

- boxes must be well-formed and inside page bounds;
- entry boxes must be at least 8x8 pt (12 pt tall for text/dropdown);
- no two entry boxes on same page may overlap (second and later fields
  of overlapping cluster get flagged);
- label must sit within 150 pt of its entry box and must not overlap it.

Exit code 0 = clean, 1 = at least one problem. JSON report lists
per-field `problems`. Lint spec BEFORE building.

## Visual review loop

```bash
python3 scripts/pdf_form_layout.py spec.json --render-overlay overlay.png [--pdf built.pdf]
```

Red rectangles = entry boxes (with field names), blue = label boxes.
Without `--pdf`, overlay goes on blank page (PIL-only, always works).
With `--pdf`, real page is rasterized underneath (needs pypdfium2 or
pdftoppm; otherwise report says `"rendered": false` with install hints).
Feed PNG to `vision_analyze`; ask specifically about collisions,
alignment, stray labels.

## Radio-group quirks (reportlab + pypdf)

- reportlab requires at least two `radio()` calls per group.
  Single-option radio group produces broken field.
- Some viewers render reportlab radio appearances inconsistently after
  pypdf fill. Verify with `--fields` (data truth) plus rendered page
  image (visual truth), not either alone.
- Flattening radio groups is least reliable flatten case. Check output
  image before shipping.
