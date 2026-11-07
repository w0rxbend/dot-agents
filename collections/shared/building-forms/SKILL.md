---
name: building-forms
description: Builds form components and data collection interfaces including contact forms, registration flows, checkout processes, surveys, and settings pages. Includes 50+ input types, validation strategies, accessibility patterns (WCAG 2.1), multi-step wizards, and UX best practices. Provides decision trees from data type to component selection, validation timing guidance, and error handling patterns. Use when creating forms, collecting user input, building surveys, implementing validation, designing multi-step workflows, or ensuring form accessibility.
---

# Form Systems & Input Patterns

## When to Use This Skill

**Triggers:**
- Contact forms, login/registration flows, checkout processes
- Surveys, questionnaires, settings pages
- Validation on user inputs
- Multi-step workflows or wizards
- Form accessibility
- Structured data collection (addresses, credit cards, dates)

**Common Requests:**
- "Create a registration form with validation"
- "Build a multi-step checkout flow"
- "Add inline validation to email input"
- "Make this form accessible for screen readers"
- "Implement a survey with conditional questions"

## Universal Form Concepts

### Component Selection Framework

**The Golden Rule:** Data Type → Input Component → Validation Pattern

**Quick Reference:**
- **Short text** (<100 chars) → Text input, Email input, Password input
- **Long text** (>100 chars) → Textarea, Rich text editor, Code editor
- **Numeric** → Number input, Currency input, Slider
- **Date/Time** → Date picker, Time picker, Date range picker
- **Boolean** → Checkbox, Toggle switch
- **Single choice** → Radio group (2-7 options), Select dropdown (>7 options), Autocomplete (>15 options)
- **Multiple choice** → Checkbox group, Multi-select, Tag input
- **File/Media** → File upload, Image upload
- **Structured** → Address input, Credit card input, Phone number input

**Detailed decision tree:** See `references/decision-tree.md`

### Validation Timing Strategies

**Recommended Default: On Blur with Progressive Enhancement**

```
Field pristine (never touched): No validation
User typing: No errors shown
On blur (field loses focus): Validate and show errors
After first error: Switch to onChange for that field
On fix: Show success immediately
```

**Validation Modes:**
1. **On Submit** - Validate on form submit (simple forms)
2. **On Blur** - Validate when field loses focus (RECOMMENDED for most forms)
3. **On Change** - Validate as user types (password strength, availability checks)
4. **Debounced** - Validate after user stops typing (API-based validation)
5. **Progressive** - Start on-blur, switch to on-change after first error

**Full validation guide:** See `references/validation-concepts.md`

### Accessibility Requirements (WCAG 2.1 AA)

**Critical Patterns:**

Start with semantic HTML: native `<input>`, `<select>`, `<textarea>` when possible.

**Labels and Instructions:**
- Every input must have associated `<label>` or `aria-label`
- Labels must be visible, descriptive
- Required fields clearly marked (not by color alone)
- Never use placeholder text as label replacement
- Help text for complex inputs

**Keyboard Navigation:**
- Logical, sequential tab order
- All inputs keyboard accessible
- Custom components support arrow keys
- Escape dismisses modals/popovers
- Visible focus (outline or custom indicator)

**Error Handling:**
- Errors programmatically tied to inputs (`aria-describedby`)
- Error messages clear, actionable
- Screen readers announce errors (`aria-live`)
- Focus moves to first error on submit
- Errors not conveyed by color alone

**ARIA Attributes:**
- `aria-required="true"` for required fields
- `aria-invalid="true"` when validation fails
- `aria-describedby` links help/error text
- `role="group"` for related inputs
- `aria-live="polite"` for validation messages
- Test with screen readers: confirm ARIA attributes work

**Full accessibility checklist:** See `references/accessibility-forms.md`

### UX Best Practices

**Modern Form UX Principles (2024-2025):**

1. **Progressive Disclosure** - Show only essential fields first, reveal advanced options on demand
2. **Smart Defaults** - Pre-fill known info, suggest values from context
3. **Inline Validation with Positive Feedback** - Green checkmark on valid input, helpful error messages
4. **Mobile-First** - Large touch targets (44px minimum), fitting keyboard types
5. **Reduce Cognitive Load** - Group related fields, clear labels, examples
6. **Error Prevention** - Constraints block invalid input, autocomplete cuts typos
7. **Autosave and Recovery** - Auto-save draft state (never passwords or card data), warn before data loss

**Detailed UX patterns:** See `references/ux-patterns.md`

### Error Message Best Practices

**Good Error Message Formula:**
1. **What's wrong** - "Email address is not valid"
2. **Why it matters** - "We need this to send your receipt"
3. **How to fix** - "Format: name@example.com"

**Examples:**

❌ **Bad:** "Invalid input"
✅ **Good:** "Email address must include @ symbol (e.g., name@example.com)"

❌ **Bad:** "Error"
✅ **Good:** "Password must be at least 8 characters long"

❌ **Bad:** "Field required"
✅ **Good:** "Please enter your email address so we can send order confirmation"

**Tone Guidelines:**
- Conversational, not robotic
- Helpful, not blaming
- Specific, not generic
- Actionable, not just descriptive

## Language-Specific Implementations

### JavaScript/React (PRIMARY)

**Recommended Stack:**
- **React Hook Form** - Form state management (best performance, 8KB bundle)
- **Zod** - TypeScript-first schema validation
- **Radix UI** or **React Aria** - Accessible component primitives

**Quick Start:**
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// Define validation schema
const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    mode: 'onBlur', // Validate on blur (recommended)
  });

  const onSubmit = (data: FormData) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <label htmlFor="email">Email</label>
      <input id="email" {...register('email')} type="email" />
      {errors.email && <span role="alert">{errors.email.message}</span>}

      <label htmlFor="password">Password</label>
      <input id="password" {...register('password')} type="password" />
      {errors.password && <span role="alert">{errors.password.message}</span>}

      <button type="submit">Login</button>
    </form>
  );
}
```

**JavaScript/React docs:**
- `references/javascript/react-hook-form.md` - Full React Hook Form guide
- `references/javascript/zod-validation.md` - Zod schema validation patterns
- `examples/` - Working React examples (`examples/javascript/` for async validation and file upload)

### Python (PRIMARY)

**Recommended Stack:**
- **Pydantic** - Data validation and settings management (runtime validation, type-safe)
- **FastAPI** - Modern async web framework, automatic validation
- **WTForms** - Flask/Django form handling (with traditional frameworks)

**Quick Start (FastAPI + Pydantic v2):**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator  # EmailStr needs: pip install 'pydantic[email]'

app = FastAPI()

# Define validation schema
class LoginForm(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

@app.post("/api/login")
async def login(form_data: LoginForm):
    # Pydantic automatically validates incoming data
    # If validation fails, returns 422 with error details
    return {"message": "Login successful", "email": form_data.email}

# Example error response (automatic, HTTP 422):
# {
#   "detail": [
#     {
#       "type": "value_error",
#       "loc": ["body", "email"],
#       "msg": "value is not a valid email address: An email address must have an @-sign.",
#       "input": "bad",
#       "ctx": {"reason": "An email address must have an @-sign."}
#     }
#   ]
# }
```

**Python docs:**
- `references/python/pydantic-forms.md` - Pydantic validation patterns
- `references/python/wtforms.md` - WTForms for Flask/Django
- `examples/python/` - Working Python examples

### Rust (FUTURE)

**Planned Libraries:**
- **validator** - Struct field validation
- **Leptos** / **Yew** - Reactive web frameworks

### Go (FUTURE)

**Planned Libraries:**
- **Templ** - Type-safe HTML templating
- **html/template** - Standard library templating

## Component Tiers

### Tier 1: Basic Input Components

**Text-Based:**
- Text field (single-line)
- Textarea (multi-line)
- Email input (validation)
- Password input (visibility toggle)
- Number input (step controls)
- Tel input (formatting)
- URL input (protocol validation)
- Search input (clear button)

**Selection:**
- Radio group (2-7 options)
- Checkbox (boolean or multiple)
- Toggle switch (clear on/off states)
- Select dropdown (many options)
- Multi-select (multiple selections)

**Date & Time:**
- Date picker (calendar interface)
- Time picker (hour/minute)
- Date range picker (start, end)
- DateTime picker (combined)

### Tier 2: Rich Input Components

**Advanced Selection:**
- Autocomplete/Combobox (type to filter)
- Tag input (multiple tags)
- Transfer list (move items between lists)
- Listbox (keyboard-navigable)

**Specialized:**
- Color picker (hex, RGB, HSL)
- File uploader (single, multiple, drag-drop)
- Image uploader (crop, resize, preview)
- Slider/Range (single or range)
- Rating input (stars, numeric, emoji)
- Rich text editor (formatting, media)
- Code editor (syntax highlighting)
- Markdown editor (preview, toolbar)

**Structured Data:**
- Address input (multi-field)
- Credit card input (formatted)
- Phone number (international)
- Currency input (symbol, decimal)

### Tier 3: Complex Form Patterns

**Multi-Step Forms:**
- Linear wizard (step 1 → 2 → 3)
- Branching wizard (conditional steps)
- Progress indicators
- Save and resume (draft state)
- Review and submit page

**Dynamic Forms:**
- Conditional fields (show/hide)
- Repeating sections (add/remove)
- Field arrays (dynamic list)
- Nested forms (complex objects)

**Advanced Patterns:**
- Inline editing (click to edit)
- Bulk editing (multiple records)
- Autosave (periodic or on change)
- Optimistic updates
- Undo/redo

## Integration with Design Tokens

Style form components with design tokens (CSS custom properties) for theme switching (light/dark/high-contrast/custom brands).

**Key Token Categories:**
- **Color** - Input backgrounds, borders, text, error/success states
- **Spacing** - Padding, gaps between fields, label margins
- **Typography** - Font sizes, weights for inputs, labels, errors
- **Borders** - Border width, radius, focus ring
- **Shadows** - Focus indicators, elevation

**See:** theming-components skill for full theming docs.

## Common Use Cases

### Contact Form
```tsx
// Basic contact form with validation
// See: examples/basic-form.tsx
```

### Registration Flow
```tsx
// Multi-step registration with password strength
// See: examples/multi-step-wizard.tsx
```

### Inline Validation
```tsx
// Real-time validation with debouncing
// See: examples/inline-validation.tsx
```

### Survey with Conditional Logic
```tsx
// Dynamic form with conditional fields
// See: examples/conditional-form.tsx
```

### Settings Page
```tsx
// Mixed input types with autosave
// See: examples/settings-form.tsx
```

## Quick Decision Guide

**Question: How to handle complex validation?**
→ Schema validation (Zod for TypeScript, Yup for JavaScript)
→ See `references/javascript/zod-validation.md` for patterns

**Question: How to build multi-step form?**
→ State management with progress tracking
→ See `examples/multi-step-wizard.tsx`
