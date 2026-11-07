# Media Implementation Guide

## File Upload Selection

### Basic Upload (<10MB)
- Single file
- Simple validation
- Preview
- Progress indicator

### Advanced Upload (>10MB)
- Chunked uploads
- Resume
- Queue management
- Multiple files

### Cloud Direct Upload
- Large files (>100MB)
- Less server load
- CDN integration
- Client-side signing

## Image Display Selection

### Static Gallery
- Fixed image count
- Grid layout
- Click to expand

### Dynamic Gallery
- Lazy loading
- Infinite scroll
- Search/filter

### Carousel/Slider
- Sequential display
- Optional auto-play
- Navigation controls

## Video Implementation Selection

### Native HTML5
- Simple requirements
- Basic controls
- No streaming needed

### Custom Player (video.js)
- Advanced features
- Plugin support
- Adaptive streaming

### Cloud Video (Vimeo/YouTube)
- Hosted
- No transcoding
- Embed controls

## Performance Thresholds

| Media Type | Threshold | Optimization |
|------------|-----------|--------------|
| Images | >500KB | Compression, WebP, responsive |
| Video | >50MB | Streaming, transcoding |
| Audio | >5MB | Compression, streaming |
| Documents | >10MB | Lazy loading, pagination |

## See Also
- `upload-patterns.md` - Upload implementations
- `gallery-patterns.md` - Gallery designs
- `video-player.md` - Video player setup
