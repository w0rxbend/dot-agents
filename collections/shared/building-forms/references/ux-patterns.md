# Form UX Patterns & Best Practices

## Table of Contents

- [Core UX Principles for Forms](#core-ux-principles-for-forms)
  - [The Three Goals of Excellent Form UX](#the-three-goals-of-excellent-form-ux)
- [Modern Form UX Patterns (2024-2025)](#modern-form-ux-patterns-2024-2025)
  - [1. Progressive Disclosure](#1-progressive-disclosure)
  - [2. Smart Defaults](#2-smart-defaults)
  - [3. Inline Validation with Positive Feedback](#3-inline-validation-with-positive-feedback)
  - [4. Mobile-First Considerations](#4-mobile-first-considerations)
  - [5. Reduce Cognitive Load](#5-reduce-cognitive-load)
  - [6. Error Prevention](#6-error-prevention)
  - [7. Autosave and Recovery](#7-autosave-and-recovery)
- [UX Anti-Patterns (What NOT to Do)](#ux-anti-patterns-what-not-to-do)
  - [Common UX Mistakes](#common-ux-mistakes)
- [UX Testing Checklist](#ux-testing-checklist)
  - [Manual Testing](#manual-testing)
  - [Analytics to Monitor](#analytics-to-monitor)
- [Next Steps](#next-steps)

## Core UX Principles for Forms

### The Three Goals of Excellent Form UX

1. **Minimize user effort** - Less typing, clicks and cognitive load
2. **Prevent errors** - Design out mistakes up front
3. **Provide clear feedback** - Users see what's happening

---

## Modern Form UX Patterns (2024-2025)

### 1. Progressive Disclosure

**Principle:** Show essential fields first, advanced options on demand.

**When to Use:**
- 10+ fields
- Mix of required and optional fields
- Advanced/expert settings
- Fields conditional on user type

---

#### Pattern 1A: Show More / Show Less

```html
<!-- Initial view: Essential fields only -->
<form>
  <input type="text" id="name" placeholder="Name" />
  <input type="email" id="email" placeholder="Email" />
  <input type="tel" id="phone" placeholder="Phone" />

  <!-- Optional fields (hidden initially) -->
  <div id="optional-fields" hidden>
    <input type="text" id="company" placeholder="Company (optional)" />
    <input type="text" id="title" placeholder="Job Title (optional)" />
    <input type="url" id="website" placeholder="Website (optional)" />
  </div>

  <button type="button" onclick="toggleOptional()">
    + Show more fields
  </button>

  <button type="submit">Submit</button>
</form>
```

**Best Practices:**
- ✅ Mark optional fields clearly
- ✅ Label "Show more fields", not just "More"
- ✅ Change text when expanded ("Show less fields")
- ✅ Keep scroll position on toggle

---

#### Pattern 1B: Accordion Sections

```html
<form>
  <!-- Section 1: Always visible (required) -->
  <fieldset>
    <legend>Personal Information</legend>
    <input type="text" name="name" required />
    <input type="email" name="email" required />
  </fieldset>

  <!-- Section 2: Collapsible (optional) -->
  <details>
    <summary>Shipping Address (Optional)</summary>
    <fieldset>
      <input type="text" name="street" />
      <input type="text" name="city" />
      <input type="text" name="zip" />
    </fieldset>
  </details>

  <!-- Section 3: Collapsible (optional) -->
  <details>
    <summary>Additional Preferences (Optional)</summary>
    <fieldset>
      <label>
        <input type="checkbox" name="newsletter" />
        Subscribe to newsletter
      </label>
      <label>
        <input type="checkbox" name="notifications" />
        Enable notifications
      </label>
    </fieldset>
  </details>

  <button type="submit">Submit</button>
</form>
```

**Best Practices:**
- ✅ Use `<details>` and `<summary>` for native accordion
- ✅ Auto-expand sections with errors
- ✅ Remember user's expansion preferences
- ✅ Show section status (incomplete/complete)

---

#### Pattern 1C: Conditional Fields (Show Based on Answer)

```html
<form>
  <label>
    <input type="radio" name="account-type" value="personal" />
    Personal Account
  </label>
  <label>
    <input type="radio" name="account-type" value="business" />
    Business Account
  </label>

  <!-- Show only if "business" selected -->
  <div id="business-fields" hidden>
    <input type="text" name="company-name" placeholder="Company Name" />
    <input type="text" name="tax-id" placeholder="Tax ID" />
  </div>

  <button type="submit">Continue</button>
</form>

<script>
  document.querySelectorAll('[name="account-type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      document.getElementById('business-fields').hidden =
        e.target.value !== 'business';
    });
  });
</script>
```

**Best Practices:**
- ✅ Show/hide immediately on selection change
- ✅ Clear values of hidden fields
- ✅ Don't validate hidden fields
- ✅ Announce changes to screen readers (`aria-live`)

---

### 2. Smart Defaults

**Principle:** Pre-fill known info, suggest values, remember past entries.

---

#### Pattern 2A: Auto-detect Values

```javascript
// Auto-detect timezone
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
document.getElementById('timezone').value = timezone;

// Auto-detect language
const language = navigator.language || 'en-US';
document.getElementById('language').value = language;

// Auto-detect country (from IP - server-side)
fetch('/api/detect-country')
  .then(res => res.json())
  .then(data => {
    document.getElementById('country').value = data.country;
  });
```

**What to Auto-Detect:**
- Timezone
- Language/locale
- Country (from IP)
- Currency (from country)
- Date format preference

---

#### Pattern 2B: Remember Previous Entries

```javascript
// Save form data to localStorage
form.addEventListener('input', (e) => {
  localStorage.setItem(e.target.name, e.target.value);
});

// Restore on page load
document.addEventListener('DOMContentLoaded', () => {
  form.querySelectorAll('[name]').forEach(input => {
    const saved = localStorage.getItem(input.name);
    if (saved) input.value = saved;
  });
});

// Clear after successful submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const success = await submitForm();
  if (success) {
    localStorage.clear();
  }
});
```

**Best Practices:**
- ✅ Restore on refresh
- ✅ Clear after successful submit
- ✅ Respect privacy (don't save sensitive data like passwords)

---

#### Pattern 2C: Suggest Based on Context

```html
<!-- Email suggestion based on common domains -->
<input
  type="email"
  id="email"
  list="email-suggestions"
/>
<datalist id="email-suggestions">
  <option value="@gmail.com">
  <option value="@yahoo.com">
  <option value="@outlook.com">
  <option value="@hotmail.com">
</datalist>

<!-- Address autocomplete (Google Places API) -->
<input
  type="text"
  id="address"
  placeholder="Start typing address..."
  autocomplete="street-address"
/>
```

**What to Suggest:**
- Email domains (@gmail.com)
- Common addresses (via Google Places, USPS)
- Product names, categories
- Previous values
- Common responses

---

### 3. Inline Validation with Positive Feedback

**Principle:** Real-time feedback with errors and success indicators.

---

#### Pattern 3A: Success Indicators

```html
<div class="field">
  <label for="email">Email</label>
  <input type="email" id="email" aria-describedby="email-status" />

  <!-- Error state -->
  <p id="email-error" class="error-message" hidden>
    Please enter a valid email address
  </p>

  <!-- Success state (NEW in modern UX) -->
  <p id="email-success" class="success-message" hidden>
    <span aria-hidden="true">✓</span> Valid email format
  </p>
</div>

<style>
  /* Visual feedback via border color */
  .field input.valid {
    border-color: #22c55e; /* Green */
  }

  .field input.invalid {
    border-color: #ef4444; /* Red */
  }

  .success-message {
    color: #22c55e;
    font-size: 0.875rem;
  }

  .error-message {
    color: #ef4444;
    font-size: 0.875rem;
  }
</style>
```

**Best Practices:**
- ✅ Green checkmark when field valid
- ✅ Color + icon (not color alone)
- ✅ Clear success message when field changes
- ⚠️ Don't overuse (checkmark on every field distracts)

---

#### Pattern 3B: Password Strength Meter

```html
<div class="field">
  <label for="password">Password</label>
  <input
    type="password"
    id="password"
    aria-describedby="password-strength password-requirements"
  />

  <!-- Strength meter -->
  <div id="password-strength" class="strength-meter">
    <div class="strength-bar" data-strength="weak"></div>
    <span class="strength-text">Weak</span>
  </div>

  <!-- Requirements checklist -->
  <ul id="password-requirements" class="requirements">
    <li data-met="false">✗ At least 8 characters</li>
    <li data-met="false">✗ Contains uppercase letter</li>
    <li data-met="false">✗ Contains number</li>
    <li data-met="false">✗ Contains special character</li>
  </ul>
</div>

<script>
  passwordInput.addEventListener('input', (e) => {
    const value = e.target.value;
    const strength = calculateStrength(value); // weak, medium, strong

    // Update strength meter
    strengthBar.dataset.strength = strength;
    strengthText.textContent = strength.charAt(0).toUpperCase() + strength.slice(1);

    // Update requirements checklist
    updateRequirement(0, value.length >= 8);
    updateRequirement(1, /[A-Z]/.test(value));
    updateRequirement(2, /\d/.test(value));
    updateRequirement(3, /[!@#$%^&*]/.test(value));
  });
</script>
```

**Best Practices:**
- ✅ Strength meter (Weak/Medium/Strong)
- ✅ Requirements checklist
- ✅ Real-time updates (on-change)
- ✅ Visual indicators (color, icons)
- ✅ Actionable requirements

---

#### Pattern 3C: Real-Time Character Count

```html
<div class="field">
  <label for="tweet">Tweet</label>
  <textarea
    id="tweet"
    maxlength="280"
    aria-describedby="tweet-count"
  ></textarea>

  <!-- Character count -->
  <p id="tweet-count" aria-live="polite">
    <span id="current-count">0</span> / 280 characters
  </p>
</div>

<script>
  tweetTextarea.addEventListener('input', (e) => {
    const current = e.target.value.length;
    const max = 280;
    const remaining = max - current;

    currentCount.textContent = current;

    // Warning when approaching limit
    if (remaining < 20) {
      tweetCount.classList.add('warning');
    } else {
      tweetCount.classList.remove('warning');
    }

    // Error when over limit (if not using maxlength)
    if (remaining < 0) {
      tweetCount.classList.add('error');
    } else {
      tweetCount.classList.remove('error');
    }
  });
</script>
```

**Best Practices:**
- ✅ Show current count, not just remaining
- ✅ Warn near limit (last 20 characters)
- ✅ `aria-live="polite"` for screen reader announcements
- ✅ Weigh soft limit (warn) vs hard limit (prevent)

---

### 4. Mobile-First Considerations

**Principle:** Design for mobile first, enhance for desktop.

**Mobile Challenges:**
- Small screens
- Touch input (needs larger targets)
- Virtual keyboards (vary by type)
- Variable connectivity (plan for offline)

---

#### Pattern 4A: Appropriate Input Types

```html
<!-- Email input → Shows @ key -->
<input type="email" autocomplete="email" />

<!-- Phone input → Shows numeric keypad -->
<input type="tel" autocomplete="tel" />

<!-- Number input → Shows numeric keyboard -->
<input type="number" inputmode="numeric" />

<!-- URL input → Shows .com key -->
<input type="url" autocomplete="url" />

<!-- Date input → Shows native date picker -->
<input type="date" />

<!-- Numeric code (OTP) → Numeric keyboard without spinners -->
<input type="text" inputmode="numeric" pattern="[0-9]*" autocomplete="one-time-code" />
```

**Mobile Keyboard Types:**

| Input Type | Mobile Keyboard | Best For |
|------------|-----------------|----------|
| `type="email"` | Email keyboard (@, .) | Email addresses |
| `type="tel"` | Numeric dialpad | Phone numbers |
| `type="number"` | Numeric with +/- | Quantities, ages |
| `type="url"` | URL keyboard (.com, /) | Website URLs |
| `type="search"` | Search keyboard (Go) | Search queries |
| `inputmode="numeric"` | Numeric only | Credit cards, OTP codes |
| `inputmode="decimal"` | Numeric with decimal | Prices, measurements |

**Best Practices:**
- ✅ Semantic input types (email, tel, url)
- ✅ `inputmode` for numeric inputs without spinners
- ✅ `autocomplete` attributes for autofill

---

#### Pattern 4B: Large Touch Targets

```css
/* Minimum touch target: 44x44px (iOS), 48x48px (Android) */
.button,
.input,
.checkbox,
.radio {
  min-height: 44px;
  min-width: 44px;
}

/* Increase clickable area with padding */
label {
  padding: 12px;
  cursor: pointer;
}

/* Checkbox/radio: Larger click area */
.checkbox-wrapper,
.radio-wrapper {
  position: relative;
  min-height: 44px;
  display: flex;
  align-items: center;
}

.checkbox-wrapper input[type="checkbox"],
.radio-wrapper input[type="radio"] {
  width: 24px;
  height: 24px;
  margin-right: 12px;
}

/* Make entire label clickable */
.checkbox-wrapper label,
.radio-wrapper label {
  flex: 1;
  cursor: pointer;
}
```

**Best Practices:**
- ✅ Minimum 44x44px touch targets (iOS HIG)
- ✅ Minimum 48x48px recommended (Material Design)
- ✅ Padding to enlarge clickable area
- ✅ Whole label clickable (not just checkbox)
- ✅ 8px minimum spacing between targets

---

#### Pattern 4C: Single-Column Layout

```css
/* Mobile-first: Single column */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  width: 100%;
}

/* Desktop: Multi-column when space allows */
@media (min-width: 768px) {
  .form-fields.two-column {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem 2rem;
  }

  /* Some fields span full width */
  .field.full-width {
    grid-column: 1 / -1;
  }
}
```

**Best Practices:**
- ✅ Single column on mobile (default)
- ✅ Multi-column on desktop (when helpful)
- ✅ Related fields side-by-side (first/last name)
- ✅ Long fields full-width (address, description)
- ✅ Labels above inputs (not beside) on mobile

---

#### Pattern 4D: Sticky Submit Button (Mobile)

```html
<form>
  <!-- Form fields -->
  <div class="form-fields">
    <!-- inputs here -->
  </div>

  <!-- Sticky footer on mobile -->
  <div class="form-footer">
    <button type="submit" class="submit-button">
      Submit Form
    </button>
  </div>
</form>

<style>
  /* Mobile: Sticky submit button */
  @media (max-width: 767px) {
    .form-footer {
      position: sticky;
      bottom: 0;
      background: white;
      padding: 1rem;
      border-top: 1px solid #e5e7eb;
      box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }

    .submit-button {
      width: 100%;
      min-height: 48px;
      font-size: 1rem;
      font-weight: 600;
    }
  }

  /* Desktop: Normal flow -->
  @media (min-width: 768px) {
    .form-footer {
      margin-top: 2rem;
    }
  }
</style>
```

**Best Practices:**
- ✅ Sticky submit button on long forms (mobile)
- ✅ Full-width button on mobile
- ✅ Clear visual separation (border, shadow)
- ✅ Show progress indicator if multi-step
- ❌ Don't hide submit button below fold

---

### 5. Reduce Cognitive Load

#### Pattern 5A: One Question Per Page (When Appropriate)

```html
<!-- Multi-step form: One question per page -->

<!-- Step 1: What's your name? -->
<form>
  <h2>What's your name?</h2>
  <input type="text" name="name" placeholder="Enter your full name" />
  <button type="submit">Continue</button>
</form>

<!-- Step 2: What's your email? -->
<form>
  <h2>What's your email address?</h2>
  <input type="email" name="email" placeholder="name@example.com" />
  <button type="submit">Continue</button>
</form>

<!-- Step 3: Choose a password -->
<form>
  <h2>Choose a password</h2>
  <input type="password" name="password" />
  <div class="strength-meter"><!-- ... --></div>
  <button type="submit">Continue</button>
</form>
```

**When to Use:**
- ✅ Complex decisions (need thought)
- ✅ Mobile-first apps
- ✅ Conversational interfaces (chatbot-like)
- ✅ Progressive profiling (collect data over time)

**When NOT to Use:**
- ❌ Short forms (3-5 fields)
- ❌ Related fields (address fields together)
- ❌ Desktop-focused apps
- ❌ Power users (prefer speed over simplicity)

---

#### Pattern 5B: Group Related Fields

```html
<form>
  <!-- Personal Information group -->
  <fieldset>
    <legend>Personal Information</legend>
    <div class="field-group">
      <div class="field">
        <label for="first-name">First Name</label>
        <input type="text" id="first-name" />
      </div>
      <div class="field">
        <label for="last-name">Last Name</label>
        <input type="text" id="last-name" />
      </div>
    </div>
  </fieldset>

  <!-- Contact Information group -->
  <fieldset>
    <legend>Contact Information</legend>
    <div class="field">
      <label for="email">Email</label>
      <input type="email" id="email" />
    </div>
    <div class="field">
      <label for="phone">Phone</label>
      <input type="tel" id="phone" />
    </div>
  </fieldset>

  <button type="submit">Submit</button>
</form>
```

**Best Practices:**
- ✅ Use `<fieldset>` and `<legend>` for semantic grouping
- ✅ Visual separation between groups (spacing, borders)
- ✅ Clear group labels (`<legend>`)

---

#### Pattern 5C: Clear, Concise Labels

```html
<!-- ❌ Unclear labels -->
<label>Input 1</label>
<input type="text" />

<label>Data</label>
<input type="text" />

<!-- ✅ Clear, specific labels -->
<label>First Name</label>
<input type="text" placeholder="John" />

<label>Email Address</label>
<input type="email" placeholder="john@example.com" />

<!-- ✅ Labels with examples -->
<label>
  Phone Number
  <span class="example">(e.g., 555-123-4567)</span>
</label>
<input type="tel" placeholder="555-123-4567" />

<!-- ✅ Labels with help text -->
<label for="username">
  Username
  <span class="help-text">This will be visible to other users</span>
</label>
<input type="text" id="username" />
```

**Best Practices:**
- ✅ Clear, descriptive labels
- ✅ Examples when helpful
- ✅ Explain why data is needed (privacy concern)
- ✅ Short labels (1-3 words ideal)
- ❌ No technical jargon
- ❌ No ambiguous terms ("Data", "Input 1")

---

#### Pattern 5D: Show Character/Word Count

```html
<div class="field">
  <label for="bio">Bio (Max 200 characters)</label>
  <textarea id="bio" maxlength="200" aria-describedby="bio-count"></textarea>
  <p id="bio-count" class="character-count">
    <span id="current">0</span> / 200 characters
  </p>
</div>

<div class="field">
  <label for="essay">Essay (500-1000 words)</label>
  <textarea id="essay" aria-describedby="essay-count"></textarea>
  <p id="essay-count" class="word-count">
    <span id="words">0</span> words (minimum 500)
  </p>
</div>
```

**Best Practices:**
- ✅ Character count for limited fields (tweets, bios)
- ✅ Word count for essays, descriptions
- ✅ `aria-live="polite"` for screen reader updates

---

### 6. Error Prevention

#### Pattern 6A: Constraints Prevent Invalid Input

```html
<!-- Numeric input: Prevent non-numeric -->
<input type="number" min="1" max="100" step="1" />

<!-- Date input: Prevent past dates -->
<input type="date" min="2025-01-01" />

<!-- Time input: Specific time intervals -->
<input type="time" step="900" /> <!-- 15-minute intervals -->

<!-- Text input: Max length -->
<input type="text" maxlength="20" />

<!-- Pattern validation (credit card) -->
<input
  type="text"
  pattern="[0-9]{13,19}"
  title="Credit card number (13-19 digits)"
/>
```

**Best Practices:**
- ✅ `min`, `max` for numeric/date ranges
- ✅ `maxlength` for character limits
- ✅ `pattern` for specific formats
- ✅ `step` for specific increments
- ⚠️ Don't block input entirely (allow paste, then validate)

---

#### Pattern 6B: Autocomplete Reduces Typos

```html
<!-- Browser autocomplete -->
<input type="text" name="name" autocomplete="name" />
<input type="email" name="email" autocomplete="email" />
<input type="tel" name="phone" autocomplete="tel" />
<input type="text" name="street" autocomplete="street-address" />
<input type="text" name="city" autocomplete="address-level2" />
<input type="text" name="state" autocomplete="address-level1" />
<input type="text" name="zip" autocomplete="postal-code" />
<input type="text" name="country" autocomplete="country-name" />

<!-- Credit card autocomplete -->
<input type="text" autocomplete="cc-number" />
<input type="text" autocomplete="cc-name" />
<input type="text" autocomplete="cc-exp" />
<input type="text" autocomplete="cc-csc" />
```

**Autocomplete Attribute Values:**
- `name` - Full name
- `given-name` - First name
- `family-name` - Last name
- `email` - Email address
- `tel` - Phone number
- `street-address` - Street address
- `address-level1` - State/province
- `address-level2` - City
- `postal-code` - ZIP/postal code
- `country-name` - Country
- `cc-number` - Credit card number
- `cc-exp` - Credit card expiry

**Best Practices:**
- ✅ Autocomplete attributes on common fields
- ✅ Required for accessibility (WCAG 1.3.5, Level AA)

---

#### Pattern 6C: Confirmation Fields (When Necessary)

```html
<!-- Password confirmation -->
<div class="field">
  <label for="password">Password</label>
  <input type="password" id="password" name="password" />
</div>

<div class="field">
  <label for="confirm-password">Confirm Password</label>
  <input
    type="password"
    id="confirm-password"
    name="confirm-password"
    aria-describedby="confirm-error"
  />
  <p id="confirm-error" class="error-message" hidden>
    Passwords do not match
  </p>
</div>

<!-- Email confirmation (use sparingly) -->
<div class="field">
  <label for="email">Email Address</label>
  <input type="email" id="email" name="email" />
</div>

<div class="field">
  <label for="confirm-email">Confirm Email</label>
  <input
    type="email"
    id="confirm-email"
    name="confirm-email"
    aria-describedby="email-confirm-error"
  />
</div>
```

**When to Use Confirmation Fields:**
- ✅ Passwords (prevent account lockout)
- ✅ Email (prevents wrong receipts, hard to recover)
- ✅ Irreversible actions (account deletion)

**When NOT to Use:**
- ❌ Most fields (adds friction)
- ❌ When autocomplete available
- ❌ When email/phone verification available
- ❌ When undo possible

---

### 7. Autosave and Recovery

**Principle:** Autosave to prevent data loss.

---

#### Pattern 7A: Autosave Draft

```javascript
// Autosave every 30 seconds
let autosaveTimer;

form.addEventListener('input', () => {
  clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(() => {
    saveDraft();
  }, 30000); // 30 seconds
});

async function saveDraft() {
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  await fetch('/api/save-draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  showSaveStatus('Draft saved');
}

// Show save status
function showSaveStatus(message) {
  const status = document.getElementById('save-status');
  status.textContent = message;
  status.setAttribute('aria-live', 'polite');
}
```

**Best Practices:**
- ✅ Autosave every 30-60 seconds
- ✅ Save on field blur
- ✅ Show "Last saved at" timestamp
- ✅ Debounce to avoid excessive saves
- ✅ Server-side or localStorage

---

#### Pattern 7B: Warn Before Leaving

```javascript
let hasUnsavedChanges = false;

form.addEventListener('input', () => {
  hasUnsavedChanges = true;
});

form.addEventListener('submit', () => {
  hasUnsavedChanges = false;
});

// Warn before leaving page
window.addEventListener('beforeunload', (e) => {
  if (hasUnsavedChanges) {
    e.preventDefault();
    e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    return e.returnValue;
  }
});
```

**Best Practices:**
- ✅ Warn only on unsaved changes
- ✅ Clear warning after successful submit
- ✅ Native browser dialog (can't customize much)
- ✅ Combine with autosave

---

#### Pattern 7C: Resume Where User Left Off

```javascript
// Save form state to localStorage
function saveFormState() {
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);
  localStorage.setItem('form-draft', JSON.stringify(data));
  localStorage.setItem('form-draft-timestamp', Date.now());
}

// Restore form state
function restoreFormState() {
  const draft = localStorage.getItem('form-draft');
  const timestamp = localStorage.getItem('form-draft-timestamp');

  if (draft && timestamp) {
    const age = Date.now() - parseInt(timestamp);
    const daysOld = age / (1000 * 60 * 60 * 24);

    // Only restore if less than 7 days old
    if (daysOld < 7) {
      const data = JSON.parse(draft);
      Object.entries(data).forEach(([name, value]) => {
        const input = form.elements[name];
        if (input) input.value = value;
      });

      showNotification('Draft restored from ' + new Date(parseInt(timestamp)).toLocaleDateString());
    } else {
      // Clear old drafts
      localStorage.removeItem('form-draft');
      localStorage.removeItem('form-draft-timestamp');
    }
  }
}

// Run on page load
document.addEventListener('DOMContentLoaded', restoreFormState);
```

**Best Practices:**
- ✅ Notify on draft restore
- ✅ Expire old drafts (7-30 days)
- ✅ Let user discard draft

---

## UX Anti-Patterns (What NOT to Do)

### Common UX Mistakes

❌ **Captcha for every form**
- Accessibility issues (vision, cognitive)
- Use only when spam is real problem
- Alternatives: honeypot, rate limiting, reCAPTCHA v3

❌ **Required fields not indicated**
- User doesn't know what's required until submit error
- Mark required fields clearly (* or "(required)")

❌ **Disabled submit button without explanation**
- User doesn't know why submit is blocked
- Allow submit, then show errors
- Or show clear message ("Complete all required fields")

❌ **Too many required fields**
- Asks for unneeded info
- High abandonment
- Require only what's absolutely necessary

❌ **Long forms without progress indication**
- User doesn't know how much remains
- Use progress bar or step indicator
- Consider multi-step

❌ **Unclear error messages**
- "Invalid input" (what's wrong?)
- "Error" (not helpful)
- Use specific, actionable messages

❌ **Reset button next to submit**
- Accidental click clears whole form
- Rarely needed (users can clear manually)
- Remove reset button entirely

❌ **Placeholders as labels**
- Disappears when user types (confusion)
- Accessibility issue (screen readers)
- Use explicit `<label>` instead

---

## UX Testing Checklist

### Manual Testing

- [ ] Complete form on real mobile device (iOS and Android)
- [ ] All input keyboards (email shows @, tel shows numbers)
- [ ] Autofill/autocomplete works
- [ ] Low connectivity (slow network)
- [ ] Form interruption (leave page, come back)
- [ ] Autosave (wait 30 seconds, refresh page)
- [ ] Measure completion time (aim for <2 minutes for most forms)
- [ ] Validation timing (not too early, not too late)
- [ ] Error messages clear and helpful
- [ ] Success indicators show when field valid

### Analytics to Monitor

- **Completion rate** - % of users who start and finish form
- **Time to complete** - Average start-to-submit time
- **Abandonment points** - Fields where users leave
- **Error rate per field** - Fields with most validation errors
- **Field interaction time** - Time spent per field
- **Device breakdown** - Mobile vs desktop completion rates

---

## Next Steps

- Ensure accessibility compliance → `accessibility-forms.md`
- Implement validation strategies → `validation-concepts.md`
- Choose component types → `decision-tree.md`
- Pick language implementation:
  - JavaScript/React → `javascript/react-hook-form.md`
  - Python → `python/pydantic-forms.md`
