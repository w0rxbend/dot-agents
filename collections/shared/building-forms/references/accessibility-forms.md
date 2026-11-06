# Form Accessibility: WCAG 2.1 AA Compliance

## Table of Contents

- [Essential Accessibility Patterns](#essential-accessibility-patterns)
  - [1. Labels and Instructions](#1-labels-and-instructions)
  - [2. Keyboard Navigation](#2-keyboard-navigation)
  - [3. Error Handling](#3-error-handling)
  - [4. ARIA Attributes for Forms](#4-aria-attributes-for-forms)
  - [5. Color and Contrast](#5-color-and-contrast)
  - [6. Screen Reader Support](#6-screen-reader-support)
  - [7. Timing and Limits](#7-timing-and-limits)
- [Accessibility Testing Checklist](#accessibility-testing-checklist)
  - [Automated Testing](#automated-testing)
  - [Manual Testing](#manual-testing)
- [Common Accessibility Anti-Patterns](#common-accessibility-anti-patterns)
  - [What NOT to Do](#what-not-to-do)
- [Resources](#resources)
- [Next Steps](#next-steps)

## Essential Accessibility Patterns

### 1. Labels and Instructions

#### Every Input Must Have a Label

**Requirement:** WCAG 3.3.2 (Level A) - Labels or Instructions

**HTML Pattern:**
```html
<!-- Explicit label (RECOMMENDED) -->
<label for="email">Email Address</label>
<input type="email" id="email" name="email" required />

<!-- Implicit label (acceptable but less flexible) -->
<label>
  Email Address
  <input type="email" name="email" required />
</label>

<!-- aria-label (when visual label not possible) -->
<input type="email" name="email" aria-label="Email Address" required />

<!-- aria-labelledby (label from another element) -->
<h3 id="email-heading">Email Address</h3>
<input type="email" name="email" aria-labelledby="email-heading" required />
```

**Best Practices:**
- ✅ Use explicit `<label>` with `for` attribute pointing to input `id`
- ✅ Keep labels visible and persistent (not only placeholders)
- ✅ Make labels descriptive ("Email address" not "Input")
- ❌ Never use placeholder as sole label (disappears on typing)
- ❌ Don't hide labels visually unless using `aria-label`

---

#### Required Field Indicators

**Requirement:** WCAG 1.4.1 (Level A) - Use of Color

**Pattern:**
```html
<!-- Text-based indicator (REQUIRED) -->
<label for="username">
  Username <span aria-label="required">*</span>
</label>
<input type="text" id="username" required aria-required="true" />

<!-- Or use "(required)" text -->
<label for="password">
  Password <span class="required-text">(required)</span>
</label>
<input type="password" id="password" required aria-required="true" />

<!-- Add legend for entire form -->
<p class="form-instructions">
  Fields marked with <span aria-label="asterisk">*</span> are required.
</p>
```

**Best Practices:**
- ✅ Use text or symbol ("*", "(required)"), not only color
- ✅ Add `required` attribute to input
- ✅ Add `aria-required="true"` for screen readers
- ✅ Add legend explaining indicator meaning
- ❌ Don't rely on color alone (red label text)

---

#### Help Text and Instructions

**Requirement:** WCAG 3.3.2 (Level A) - Labels or Instructions

**Pattern:**
```html
<label for="password">Password</label>
<input
  type="password"
  id="password"
  aria-describedby="password-help"
  required
/>
<p id="password-help" class="help-text">
  Password must be at least 8 characters and include a number.
</p>
```

**Best Practices:**
- ✅ Use `aria-describedby` to link help text to input
- ✅ Show help text before interaction (don't hide in tooltip)
- ✅ Place help text between label and input, or right after input
- ❌ Don't rely on hover-only tooltips (keyboard users can't reach them)

---

### 2. Keyboard Navigation

#### Tab Order and Focus

**Requirement:** WCAG 2.1.1 (Level A) - Keyboard, WCAG 2.4.3 (Level A) - Focus Order

**Principles:**
- Logical tab order (top to bottom, left to right)
- All interactive elements keyboard accessible
- No keyboard traps (user can always move focus away)
- Current focus always visible

**HTML Pattern:**
```html
<!-- Natural tab order (recommended) -->
<form>
  <input type="text" id="name" /> <!-- tabindex 1 -->
  <input type="email" id="email" /> <!-- tabindex 2 -->
  <input type="tel" id="phone" /> <!-- tabindex 3 -->
  <button type="submit">Submit</button> <!-- tabindex 4 -->
</form>

<!-- Manual tabindex (only when necessary) -->
<input type="text" tabindex="1" />
<input type="text" tabindex="2" />

<!-- Skip to main content link (for keyboard users) -->
<a href="#main-content" class="skip-link">Skip to main content</a>
```

**Best Practices:**
- ✅ Rely on natural tab order (DOM order)
- ✅ Use `tabindex="0"` to add custom elements to tab order
- ✅ Use `tabindex="-1"` to remove from tab order (still focusable programmatically)
- ❌ Don't use `tabindex` > 0 unless absolutely necessary (breaks natural order)

---

#### Focus Indicators

**Requirement:** WCAG 2.4.7 (Level AA) - Focus Visible

**CSS Pattern:**
```css
/* Default focus outline (don't remove without replacement!) */
input:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* Custom focus ring (accessible) */
input:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.2);
}

/* NEVER do this without replacement */
input:focus {
  outline: none; /* ❌ ACCESSIBILITY VIOLATION */
}

/* If you remove outline, add visible alternative */
input:focus {
  outline: none;
  border: 2px solid #0066cc;
  box-shadow: 0 0 5px rgba(0, 102, 204, 0.5);
}
```

**Best Practices:**
- ✅ Always show visible focus indicator
- ✅ Minimum 2px thickness, high contrast
- ✅ Consistent across all form elements
- ✅ Test with keyboard navigation (Tab key)
- ❌ Never use `outline: none` without replacement
- ❌ Don't make focus indicator too subtle (low contrast)

---

#### Keyboard Shortcuts

**Common Keyboard Patterns:**

| Key | Action | Context |
|-----|--------|---------|
| **Tab** | Next element | All forms |
| **Shift + Tab** | Previous element | All forms |
| **Enter** | Submit form | Text inputs, buttons |
| **Space** | Toggle checkbox/radio | Checkboxes, radios, buttons |
| **Arrow keys** | Navigate options | Radio groups, select, custom components |
| **Escape** | Close modal/popover | Modals, tooltips, dropdowns |
| **Home** | First option | Listboxes, custom selects |
| **End** | Last option | Listboxes, custom selects |

**Implementation:**
```html
<!-- Radio group with arrow key navigation -->
<fieldset>
  <legend>Shipping Method</legend>
  <label>
    <input type="radio" name="shipping" value="standard" />
    Standard (5-7 days)
  </label>
  <label>
    <input type="radio" name="shipping" value="express" />
    Express (2-3 days)
  </label>
</fieldset>

<!-- Custom component with keyboard support -->
<div role="combobox" aria-expanded="false" aria-controls="options" tabindex="0">
  <!-- Ensure arrow keys work, Escape closes, Enter selects -->
</div>
```

---

### 3. Error Handling

#### Error Identification

**Requirement:** WCAG 3.3.1 (Level A) - Error Identification

**Pattern:**
```html
<label for="email">Email Address</label>
<input
  type="email"
  id="email"
  aria-invalid="true"
  aria-describedby="email-error"
/>
<p id="email-error" class="error-message" role="alert">
  Please enter a valid email address (e.g., name@example.com).
</p>
```

**Best Practices:**
- ✅ Use `aria-invalid="true"` when field has error
- ✅ Use `aria-describedby` to link error message to input
- ✅ Use `role="alert"` or `aria-live="polite"` for dynamic errors
- ❌ Don't use generic messages ("Invalid input")

---

#### Error Suggestions

**Requirement:** WCAG 3.3.3 (Level AA) - Error Suggestion

**Pattern:**
```html
<label for="username">Username</label>
<input
  type="text"
  id="username"
  aria-invalid="true"
  aria-describedby="username-error"
/>
<p id="username-error" class="error-message" role="alert">
  Username must be 3-20 characters long. Current length: 2 characters.
</p>

<!-- Or with suggestion -->
<p id="password-error" class="error-message" role="alert">
  Password must contain at least one uppercase letter. Try adding a capital letter.
</p>
```

**Best Practices:**
- ✅ Explain what's wrong
- ✅ Explain how to fix it
- ✅ Give example if applicable
- ✅ Use constructive, helpful tone

---

#### Error Summary

**Requirement:** WCAG 3.3.1 (Level A) - Error Identification

**Pattern:**
```html
<!-- Error summary at top of form -->
<div class="error-summary" role="alert" tabindex="-1" id="error-summary">
  <h2>There are 2 errors in this form:</h2>
  <ul>
    <li><a href="#email">Email address is required</a></li>
    <li><a href="#password">Password must be at least 8 characters</a></li>
  </ul>
</div>

<!-- JavaScript to focus error summary on submit -->
<script>
  form.addEventListener('submit', (e) => {
    if (hasErrors) {
      e.preventDefault();
      document.getElementById('error-summary').focus();
    }
  });
</script>
```

**Best Practices:**
- ✅ Place error summary at top of form
- ✅ Make summary focusable (`tabindex="-1"`)
- ✅ Move focus to summary on submit with errors
- ✅ Link each error to its field (`href="#field-id"`)
- ✅ Use `role="alert"` for screen reader announcement

---

#### Live Validation Announcements

**Requirement:** WCAG 4.1.3 (Level AA) - Status Messages

**Pattern:**
```html
<!-- Inline error with live region -->
<label for="email">Email</label>
<input
  type="email"
  id="email"
  aria-invalid="true"
  aria-describedby="email-error"
/>
<p id="email-error" class="error-message" aria-live="polite" aria-atomic="true">
  <!-- Error message appears here when validation fails -->
  Please enter a valid email address.
</p>

<!-- Success indicator -->
<p id="email-success" aria-live="polite" class="success-message">
  Email format is valid ✓
</p>
```

**ARIA Live Regions:**
- `aria-live="polite"` - Announce when user is idle (recommended for errors)
- `aria-live="assertive"` - Announce immediately (use sparingly, critical errors only)
- `aria-atomic="true"` - Read whole message, not only changes
- `role="alert"` - Equivalent to `aria-live="assertive"`

**Best Practices:**
- ✅ Update message content in place (don't add/remove element)

---

### 4. ARIA Attributes for Forms

#### Essential ARIA Attributes

**`aria-required`**
- **Purpose:** Marks field as required
- **Usage:** `<input aria-required="true" required />`
- **Note:** Use with native `required` attribute

**`aria-invalid`**
- **Purpose:** Marks field as having validation error
- **Usage:** `<input aria-invalid="true" />` (when error exists)
- **Note:** Set to `"false"` or remove when valid

**`aria-describedby`**
- **Purpose:** Links input to help text or error message
- **Usage:** `<input aria-describedby="help-text error-message" />`
- **Note:** Can reference multiple IDs (space-separated)

**`aria-labelledby`**
- **Purpose:** Labels input via another element
- **Usage:** `<input aria-labelledby="heading" />`
- **Note:** Use when label is not a `<label>` element

**`role="group"`**
- **Purpose:** Groups related form controls
- **Usage:** `<div role="group" aria-labelledby="group-label">...</div>`
- **Note:** Use for checkbox groups, related inputs

**`role="alert"`**
- **Purpose:** Important, time-sensitive message
- **Usage:** `<p role="alert">Error: Email required</p>`
- **Note:** Screen readers announce it automatically

**`aria-live`**
- **Purpose:** Announces dynamic content changes
- **Usage:** `<div aria-live="polite">...</div>`
- **Values:** `"off"`, `"polite"` (default), `"assertive"`

---

#### Complete Example with ARIA

```html
<form aria-labelledby="form-title">
  <h2 id="form-title">Registration Form</h2>

  <!-- Required field with help text -->
  <div>
    <label for="username">
      Username <span aria-label="required">*</span>
    </label>
    <input
      type="text"
      id="username"
      name="username"
      required
      aria-required="true"
      aria-invalid="false"
      aria-describedby="username-help username-error"
    />
    <p id="username-help" class="help-text">
      Username must be 3-20 characters.
    </p>
    <p id="username-error" class="error-message" aria-live="polite" hidden>
      <!-- Error appears here -->
    </p>
  </div>

  <!-- Radio group -->
  <fieldset>
    <legend>Shipping Method <span aria-label="required">*</span></legend>
    <div role="radiogroup" aria-required="true">
      <label>
        <input type="radio" name="shipping" value="standard" required />
        Standard (5-7 days)
      </label>
      <label>
        <input type="radio" name="shipping" value="express" required />
        Express (2-3 days)
      </label>
    </div>
  </fieldset>

  <!-- Submit button -->
  <button type="submit">Submit Registration</button>
</form>
```

---

### 5. Color and Contrast

#### Color Contrast Requirements

**Requirement:** WCAG 1.4.3 (Level AA) - Contrast (Minimum)

**Minimum Ratios:**
- **Normal text:** 4.5:1 contrast ratio
- **Large text (18pt+ or 14pt+ bold):** 3:1 contrast ratio
- **UI components and graphics:** 3:1 contrast ratio

**Form-Specific Applications:**
- Input text: 4.5:1 against background
- Label text: 4.5:1 against background
- Error messages: 4.5:1 against background
- Input borders: 3:1 against background (to perceive component)
- Focus indicators: 3:1 against background

**Testing Tools:**
- Chrome DevTools: Lighthouse audit, Color contrast inspection

**Examples:**
```css
/* ❌ Insufficient contrast (3:1 ratio) */
.input {
  color: #767676; /* Gray on white background */
}

/* ✅ Sufficient contrast (4.5:1 ratio) */
.input {
  color: #595959; /* Darker gray on white background */
}

/* ✅ Error message (high contrast) */
.error-message {
  color: #c00; /* Red on white background (7:1 ratio) */
}
```

---

#### Not Relying on Color Alone

**Requirement:** WCAG 1.4.1 (Level A) - Use of Color

**Anti-Pattern:**
```html
<!-- ❌ Error indicated only by red color -->
<input style="border-color: red;" />
```

**Accessible Pattern:**
```html
<!-- ✅ Error indicated by color + icon + text -->
<input
  style="border-color: red;"
  aria-invalid="true"
  aria-describedby="error"
/>
<p id="error">
  <span aria-hidden="true">❌</span>
  Email is required
</p>
```

**Best Practices:**
- ✅ Use text labels alongside color
- ✅ Use icons (✓, ❌) alongside color
- ✅ Use border styles (solid, dashed) to differentiate
- ✅ Use `aria-invalid` for screen readers
- ❌ Don't signal error/success by color alone

---

### 6. Screen Reader Support

#### Form Landmarks

**Requirement:** WCAG 1.3.1 (Level A) - Info and Relationships

**Pattern:**
```html
<!-- Use <form> element (creates form landmark) -->
<form role="form" aria-labelledby="form-title">
  <h2 id="form-title">Contact Form</h2>
  <!-- form content -->
</form>

<!-- Or explicit role -->
<div role="form" aria-labelledby="form-title">
  <h2 id="form-title">Search</h2>
  <!-- form content -->
</div>

<!-- Search landmark -->
<form role="search">
  <label for="search">Search</label>
  <input type="search" id="search" />
  <button type="submit">Search</button>
</form>
```

---

#### Fieldsets and Legends

**Requirement:** WCAG 1.3.1 (Level A) - Info and Relationships

**Pattern:**
```html
<fieldset>
  <legend>Personal Information</legend>
  <label for="first-name">First Name</label>
  <input type="text" id="first-name" />

  <label for="last-name">Last Name</label>
  <input type="text" id="last-name" />
</fieldset>

<fieldset>
  <legend>Shipping Method <span aria-label="required">*</span></legend>
  <label>
    <input type="radio" name="shipping" value="standard" />
    Standard (5-7 days)
  </label>
  <label>
    <input type="radio" name="shipping" value="express" />
    Express (2-3 days)
  </label>
</fieldset>
```

**When to Use:**
- ✅ Grouping related inputs (name fields, address fields)
- ✅ Radio button groups
- ✅ Checkbox groups
- ✅ Complex forms with multiple sections

**Screen Reader Announcement:**
When user focuses input inside fieldset:
> "Shipping Method, required, Standard (5-7 days), radio button, 1 of 2"

---

#### Progress Indicators (Multi-Step Forms)

**Requirement:** WCAG 2.4.8 (Level AA) - Location

**Pattern:**
```html
<!-- Step indicator with ARIA -->
<nav aria-label="Form progress">
  <ol class="steps">
    <li aria-current="step">
      <span class="step-number">1</span>
      Personal Info
    </li>
    <li>
      <span class="step-number">2</span>
      Shipping
    </li>
    <li>
      <span class="step-number">3</span>
      Payment
    </li>
  </ol>
</nav>

<!-- Or use aria-label on form -->
<form aria-label="Step 1 of 3: Personal Information">
  <!-- form content -->
</form>

<!-- Announce step changes -->
<div role="status" aria-live="polite" aria-atomic="true">
  Now on step 2 of 3: Shipping Information
</div>
```

**Best Practices:**
- ✅ Mark current step with `aria-current="step"`
- ✅ Announce step changes with `aria-live`
- ✅ Show total steps and current position
- ✅ Allow back navigation to previous steps

---

### 7. Timing and Limits

#### Time Limits

**Requirement:** WCAG 2.2.1 (Level A) - Timing Adjustable

**Guideline:**
- Warn user before time expires
- Give at least 20 seconds warning
- Let user turn off time limit

**Pattern:**
```html
<!-- Session timeout warning -->
<div role="alert" aria-live="assertive">
  Your session will expire in 60 seconds.
  <button type="button">Extend Session</button>
</div>
```

**Best Practices:**
- ✅ Avoid time limits when possible
- ✅ Allow extension (at least 10 times initial)
- ✅ Save draft/autosave to prevent data loss
- ❌ Don't use time limits for security (unless required)

---

#### Autosave and Data Persistence

**Requirement:** WCAG 3.3.6 (Level AAA) - Error Prevention (All)

**Pattern:**
```html
<!-- Autosave indicator -->
<form>
  <!-- form fields -->

  <div role="status" aria-live="polite">
    <span id="save-status">All changes saved</span>
  </div>
</form>

<script>
  // Autosave every 30 seconds
  setInterval(() => {
    saveFormData();
    updateStatus('All changes saved');
  }, 30000);

  // Warn before leaving page
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges()) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
  });
</script>
```

**Best Practices:**
- ✅ Autosave every 30-60 seconds
- ✅ Save each field on blur
- ✅ Warn before navigation if changes are unsaved
- ✅ Show visual "saved" indicator
- ✅ Let user resume later

---

## Accessibility Testing Checklist

### Automated Testing

- [ ] **Lighthouse** (Chrome DevTools) - Accessibility audit
- [ ] **axe DevTools** - Browser extension for detailed WCAG checks
- [ ] **WAVE** - Web accessibility evaluation tool
- [ ] **Pa11y** - CLI for automated accessibility testing

### Manual Testing

#### Keyboard Navigation
- [ ] Tab through whole form (logical order)
- [ ] All inputs reachable by keyboard
- [ ] Focus indicators visible on all elements
- [ ] Enter key submits form from any input
- [ ] Escape key closes modals/popovers
- [ ] Arrow keys navigate radio/select groups
- [ ] No keyboard traps

#### Screen Reader Testing
- [ ] Test with NVDA (Windows - free)
- [ ] Test with JAWS (Windows - commercial)
- [ ] Test with VoiceOver (macOS/iOS - built-in)
- [ ] All labels announced correctly
- [ ] Help text announced via `aria-describedby`
- [ ] Errors announced via `aria-live` or `role="alert"`
- [ ] Required fields indicated
- [ ] Fieldset legends announced
- [ ] Form landmarks navigable

#### Visual Testing
- [ ] Minimum 4.5:1 contrast (text)
- [ ] Minimum 3:1 contrast (UI components)
- [ ] Error not indicated by color alone
- [ ] Required not indicated by color alone
- [ ] Focus indicators visible (not outline: none)
- [ ] Text resizable to 200% without content loss
- [ ] Form usable at 400% zoom (WCAG 1.4.10)

#### Error Handling
- [ ] Clear error messages (what's wrong, how to fix)
- [ ] Errors linked to inputs (`aria-describedby`)
- [ ] Error summary at top of form
- [ ] Focus moves to error summary on submit
- [ ] `aria-invalid="true"` on fields with errors
- [ ] Screen reader announces errors

---

## Common Accessibility Anti-Patterns

### What NOT to Do

❌ **Placeholder-only labels**
```html
<!-- ❌ NO VISIBLE LABEL -->
<input type="email" placeholder="Email address" />

<!-- ✅ PROPER LABEL -->
<label for="email">Email address</label>
<input type="email" id="email" placeholder="name@example.com" />
```

❌ **Keyboard traps**
```html
<!-- ❌ USER CAN'T TAB OUT OF MODAL -->
<div class="modal">
  <input type="text" />
  <!-- No way to close modal with keyboard -->
</div>

<!-- ✅ KEYBOARD ACCESSIBLE MODAL -->
<div class="modal" role="dialog" aria-labelledby="modal-title">
  <button aria-label="Close" onclick="closeModal()">×</button>
  <h2 id="modal-title">Modal Title</h2>
  <input type="text" />
  <button onclick="closeModal()">Cancel</button>
  <button type="submit">Submit</button>
</div>
```

---

## Resources

**Testing Tools:**
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- WAVE Browser Extension: https://wave.webaim.org/extension/
- axe DevTools: https://www.deque.com/axe/devtools/
- Lighthouse (Chrome DevTools): Built-in

**Screen Readers:**
- NVDA (Windows, free): https://www.nvaccess.org/
- JAWS (Windows, commercial): https://www.freedomscientific.com/products/software/jaws/
- VoiceOver (macOS/iOS): Built-in

**Guidelines:**
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- WebAIM: https://webaim.org/

---

## Next Steps

Once form is accessible:
- Apply UX best practices → `ux-patterns.md`
- Implement validation patterns → `validation-concepts.md`
- Choose language implementation:
  - JavaScript/React → `javascript/react-hook-form.md`
  - Python → `python/pydantic-forms.md`
