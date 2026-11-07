# Issue Taxonomy

## Severity Levels

### Critical
Core feature completely unusable, or data loss.

**Examples:**
- Application crashes or shows blank white page
- Form submission silently loses user data
- Authentication completely broken (can't log in at all)
- Payment flow fails and charges user without completing order
- Security vulnerability (e.g., XSS, exposed credentials in console)

### High
Significantly impairs functionality, but workaround may exist.

**Examples:**
- Key button does nothing when clicked (but refreshing fixes it)
- Search returns no results for valid queries
- Form validation rejects valid input
- Page loads but critical content missing or garbled
- Navigation link leads to 404 or wrong page
- Uncaught JavaScript exceptions in console on core pages

### Medium
Noticeable, hurts user experience, but doesn't block core functionality.

**Examples:**
- Layout misaligned or overlapping on certain screen sections
- Images fail to load (broken image icons)
- Slow performance (visible loading delays > 3 seconds)
- Form field lacks proper validation feedback (no error message on bad input)
- Console warnings suggesting deprecated or misconfigured features
- Inconsistent styling between similar pages

### Low
Minor polish issues that don't affect functionality.

**Examples:**
- Typos or grammatical errors in text content
- Minor spacing or alignment inconsistencies
- Placeholder text left in production ("Lorem ipsum")
- Favicon missing
- Console info/debug messages that shouldn't be in production
- Subtle color contrast issues that don't fail WCAG requirements

## Categories

### Functional
Features don't work as expected.

- Unresponsive buttons/links
- Forms that don't submit or submit incorrectly
- Broken user flows (can't complete multi-step process)
- Incorrect data displayed
- Partially working features

### Visual
Problems with page visual presentation.

- Layout problems (overlapping elements, broken grids)
- Broken images or missing media
- Styling inconsistencies
- Responsive design failures
- Z-index issues (elements hidden behind others)
- Text overflow or truncation

### Accessibility
Issues preventing or hindering access for users with disabilities.

- Missing alt text on meaningful images
- Poor color contrast (fails WCAG AA)
- Elements not reachable via keyboard navigation
- Missing form labels or ARIA attributes
- Focus indicators missing or unclear
- Screen reader incompatible content

### Console
Issues detected in JavaScript console output.

- Uncaught exceptions and unhandled promise rejections
- Failed network requests (4xx, 5xx errors in console)
- Deprecation warnings
- CORS errors
- Mixed content warnings (HTTP resources on HTTPS page)
- Excessive console.log output left from development

### UX (User Experience)
Functionality works but experience is poor.

- Confusing navigation or information architecture
- Missing loading indicators (user doesn't know something is happening)
- No feedback after user actions (e.g., button click with no visible result)
- Inconsistent interaction patterns
- Missing confirmation dialogs for destructive actions
- Poor error messages that don't help user recover

### Content
Problems with text, media, or information on page.

- Typos and grammatical errors
- Placeholder/dummy content in production
- Outdated information
- Missing content (empty sections)
- Broken or dead external links
- Incorrect or misleading labels
