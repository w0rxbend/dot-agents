---
name: managing-media
description: Implements media and file management components including file upload (drag-drop, multi-file, resumable), image galleries (lightbox, carousel, masonry), video players (custom controls, captions, adaptive streaming), audio players (waveform, playlists), document viewers (PDF, Office), and optimization strategies (compression, responsive images, lazy loading, CDN). Use when handling files, displaying media, or building rich content experiences.
---

# Managing Media & Files

## When to Use

Use when:
- File upload (single, multiple, drag-and-drop)
- Image galleries, carousels or lightboxes
- Video or audio players
- PDF or document viewers
- Media performance optimization (responsive images, lazy loading)
- Large file uploads (chunked, resumable)
- Cloud storage integration (S3, Cloudinary)
- Media accessibility (alt text, captions, transcripts)
- Empty states for missing media

## Quick Decision Framework

Pick implementation by media type and requirements:

```
Images                  → Gallery pattern + lazy loading + responsive srcset
Videos                  → Player with controls + captions + adaptive streaming
Audio                   → Player with waveform + playlist support
Documents (PDF)         → Viewer with navigation + search + download
File Upload (<10MB)     → Basic drag-drop with preview
File Upload (>10MB)     → Chunked upload with progress + resume
Multiple Files          → Queue management + parallel uploads
```

Detailed selection criteria: `references/implementation-guide.md`.

## File Upload Patterns

### Basic Upload (<10MB)

Small files, simple requirements:
- Drag-and-drop zone with visual feedback
- Click-to-browse fallback
- File type and size validation
- Image preview thumbnails
- Progress indicator
- Reference `references/upload-patterns.md`

Example: `examples/basic-upload.tsx`

### Advanced Upload (>10MB)

Large files needing reliability:
- Chunked uploads (resume on failure)
- Parallel uploads for multiple files
- Upload queue management
- Cancel and retry controls
- Client-side compression
- Reference `references/advanced-upload.md`

Example: `examples/chunked-upload.tsx`

### Image-Specific Upload

Images needing editing:
- Crop and rotate tools
- Client-side resize before upload
- Format conversion (PNG to WebP)
- Alt text input (accessibility)
- Reference `references/image-upload.md`

Example: `examples/image-upload-crop.tsx`

## Image Display Components

### Image Gallery

Image collections:
- Grid or masonry layout
- Lazy loading (native or custom)
- Lightbox on click
- Zoom and pan controls
- Keyboard navigation (arrow keys)
- Responsive design
- Reference `references/gallery-patterns.md`

Example: `examples/image-gallery.tsx`

### Carousel/Slider

Sequential image display:
- Auto-play (optional, pausable for accessibility)
- Dot or thumbnail navigation
- Touch/swipe
- ARIA roles for accessibility
- Infinite loop option
- Reference `references/carousel-patterns.md`

Example: `examples/carousel.tsx`

### Image Optimization

Essential strategies:
- Responsive images via `srcset` and `sizes`
- Modern formats (WebP with JPG fallback)
- Progressive JPEGs
- Blur-up placeholders
- Reference `references/image-optimization.md`

## Video Components

### Video Player

Custom video playback:
- Custom or native controls
- Play/pause, volume, fullscreen
- Captions/subtitles (VTT format)
- Playback speed control
- Picture-in-picture
- Keyboard shortcuts
- Reference `references/video-player.md`

Example: `examples/video-player.tsx`

### Video Optimization

Performance strategies:
- Adaptive streaming (HLS, DASH)
- Thumbnail preview on hover
- Lazy-load off-screen videos
- Preload strategies (`metadata`, `auto`, `none`)
- Reference `references/video-optimization.md`

## Audio Components

### Audio Player

Audio playback:
- Play/pause, seek, volume controls
- Waveform visualization (optional)
- Playlists
- Download option
- Playback speed control
- Visual indicators for accessibility
- Reference `references/audio-player.md`

Example: `examples/audio-player.tsx`

## Document Viewers

### PDF Viewer

PDF display:
- Page navigation (prev/next, jump to page)
- Zoom in/out controls
- Text search within document
- Download and print options
- Thumbnail sidebar
- Reference `references/pdf-viewer.md`

Example: `examples/pdf-viewer.tsx`

### Office Document Preview

DOCX, XLSX, PPTX files:
- Read-only or editable preview
- Cloud rendering (Google Docs Viewer, Office Online; file goes to Google/Microsoft, so not for confidential docs)
- Local rendering (limited support)
- Download option
- Reference `references/office-viewer.md`

## Performance Optimization

### File Size Guidelines

Validate client-side before upload (UX only; server re-checks):
- Images: <5MB recommended
- Videos: <100MB for web, larger for cloud
- Audio: <10MB
- Documents: <25MB
- Give clear error messages
- Suggest compression tools
- Enforce size, count and type on server or in presign conditions (sniff magic bytes, not browser MIME); reject or sanitize SVG; serve uploads from separate origin with `X-Content-Type-Options: nosniff`

### Image Optimization Checklist

```bash
# Generate optimized image set (requires Pillow; run from this skill's directory)
python scripts/optimize_images.py --input image.jpg --output optimized/ --formats webp,jpg,avif --sizes 400,800,1200
```

Strategies:
- Compress before upload (client or server)
- Generate multiple sizes (thumbnails, medium, large)
- Convert to modern formats (WebP, AVIF)
- Serve via CDN with edge caching

Full guide: `references/performance-optimization.md`.

### Video Optimization Checklist

Strategies:
- Transcode to multiple qualities (360p, 720p, 1080p)
- Use CDN with edge caching
- Provide poster images

## Accessibility Requirements

### Images

- Alt text required for meaningful images
- Empty alt (`alt=""`) for decorative images
- `<figure>` and `<figcaption>` for context
- Enough color contrast for overlays
- Reference `references/accessibility-images.md`

### Videos

- Captions/subtitles for all speech
- Transcript link
- Keyboard controls (space, arrows, M for mute)
- Pause auto-play (WCAG requirement)
- Audio description track (if applicable)
- Reference `references/accessibility-video.md`

### Audio

- Transcripts available
- Visual indicators (playing, paused, volume)
- Keyboard controls
- ARIA labels for controls
- Reference `references/accessibility-audio.md`

Verify with real tooling: run axe-core (for example `@axe-core/playwright` or `npx @axe-core/cli@4.14.0 <url>`) against rendered page. Check captions, transcripts and keyboard control by hand.

Complete requirements: `references/accessibility-patterns.md`.

## Library Recommendations

### Image Gallery: react-image-gallery

Best for feature-complete galleries:
- Mobile swipe
- Fullscreen mode
- Thumbnail navigation
- Built-in lazy loading
- Responsive out of box

```bash
npm install react-image-gallery
```

Implementation: `examples/gallery-react-image.tsx`.
Docs: `/xiaolin/react-image-gallery`.

**Alternative:** LightGallery (more features, larger bundle)

### Video: video.js

Best for custom video players:
- Plugin ecosystem
- HLS and DASH support
- Accessible controls
- Theming
- Extensive documentation

```bash
npm install video.js
```

Implementation: `examples/video-js-player.tsx`.

### Audio: wavesurfer.js

Best for waveform visualization:
- Beautiful waveform display
- Timeline interactions
- Plugins
- Responsive
- Lightweight

```bash
npm install wavesurfer.js
```

Implementation: `examples/audio-waveform.tsx`.

### PDF: react-pdf

Best for PDF rendering in React:
- Page-by-page rendering
- Text selection
- Annotation layer (links, form fields) via `renderAnnotationLayer`
- Worker-based for performance

```bash
npm install react-pdf
```

Implementation: `examples/pdf-react.tsx`.

Detailed comparison: `references/library-comparison.md`.

## Design Token Integration

Style media components with design tokens (see `theming-components` skill):
- Color tokens for backgrounds, overlays, controls
- Spacing tokens for padding and gaps
- Border tokens for thumbnails and containers
- Shadow tokens for elevation
- Motion tokens for animations

Supports light, dark, high-contrast and custom themes.
Theme switching: `theming-components` skill.

Example token usage:
```css
.upload-zone {
  border: var(--upload-zone-border);
  background: var(--upload-zone-bg);
  padding: var(--upload-zone-padding);
  border-radius: var(--upload-zone-border-radius);
}

.image-gallery {
  gap: var(--gallery-gap);
}

.video-player {
  background: var(--video-player-bg);
  border-radius: var(--video-border-radius);
}
```

## Responsive Strategies

### Image Galleries

Four responsive approaches:
1. **Grid layout** - CSS Grid with auto-fit columns
2. **Masonry layout** - Pinterest-style, variable heights
3. **Carousel** - Single image on mobile, multiple on desktop
4. **Stack** - Vertical list on mobile, grid on desktop

Implementations: `examples/responsive-gallery.tsx`.

### Video Players

Responsive considerations:
- 16:9 aspect ratio container
- Full-width on mobile
- Constrained width on desktop
- Picture-in-picture for multitasking
- Touch-friendly controls (larger hit areas)

Patterns: `references/responsive-media.md`.

## Cloud Storage Integration

### Client-Side Direct Upload

For AWS S3, Cloudinary, etc.:
1. Request signed URL from backend
2. Upload directly to cloud storage
3. Notify backend of completion
4. Display uploaded media

Benefits:
- Less server load
- Faster uploads (direct to CDN)
- No file size limits on your server

Implementation: `examples/s3-direct-upload.tsx`.
Setup: `references/cloud-storage.md`.

## Testing Tools

Generate mock media:
```bash
# Generate test images (requires Pillow)
python scripts/generate_mock_images.py --count 50 --width 1600 --height 900 --output ./mock-images
```

Analyze performance with Lighthouse or WebPageTest (image weight, LCP, lazy-loading), not a custom script.

## Resources

### Scripts (Token-Free Execution)
- `scripts/optimize_images.py` - Batch resize and convert (WebP/AVIF/JPEG/PNG) with srcset output; requires Pillow
- `scripts/generate_mock_images.py` - Test image generation; requires Pillow

### Assets (Templates and Configs)
- `assets/upload-config.json` - Upload constraints and settings

## Cross-Skill Integration

Pairs with other component skills:

- **Forms**: File input fields, validation, submission
- **Feedback**: Upload progress, success/error messages
- **AI Chat**: Image attachments, file sharing
- **Dashboards**: Media widgets, thumbnails
- **Theming** (`theming-components`): visual styling via design tokens

## Next Steps

1. Identify media type (images, video, audio, documents)
2. Determine upload requirements (size, quantity, editing)
3. Choose display pattern (gallery, carousel, player, viewer)
4. Pick library or build custom solution
5. Implement accessibility requirements
6. Apply optimization strategies
7. Test performance and responsive behavior
8. Integrate cloud storage (optional)
