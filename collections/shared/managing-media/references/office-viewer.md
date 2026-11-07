# Office Document Viewer

## Microsoft Office Online Viewer

```tsx
function OfficeViewer({ fileUrl }: { fileUrl: string }) {
  const viewerUrl = `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(fileUrl)}`;

  return (
    <iframe
      src={viewerUrl}
      width="100%"
      height="600px"
      frameBorder="0"
    />
  );
}
```

**Supports:** .docx, .xlsx, .pptx

## Google Docs Viewer

```tsx
const googleViewerUrl = `https://docs.google.com/gview?url=${encodeURIComponent(fileUrl)}&embedded=true`;

<iframe src={googleViewerUrl} width="100%" height="600px" />
```

## Mammoth.js (Word to HTML)

```tsx
import mammoth from 'mammoth';
import DOMPurify from 'dompurify';

async function convertWordToHTML(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.convertToHtml({ arrayBuffer });
  return result.value;
}

function WordViewer({ file }: { file: File }) {
  const [html, setHtml] = useState('');

  useEffect(() => {
    convertWordToHTML(file).then(setHtml);
  }, [file]);

  // mammoth does no sanitizing: .docx links can carry javascript: URLs
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />;
}
```

## Best Practices

1. **Online viewers fetch file via Google/Microsoft** - Use short-lived signed URL; never for confidential files (render locally instead)
2. **Fallback to download** - If viewing fails
3. **Loading state** - iframe loads slowly
4. **Error handling** - Unsupported file types

## Resources

- Mammoth.js: https://github.com/mwilliamson/mammoth.js
- Microsoft Office Viewer: https://support.microsoft.com/en-us/office/
