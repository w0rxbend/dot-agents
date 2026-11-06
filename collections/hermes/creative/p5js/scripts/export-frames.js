#!/usr/bin/env node
/**
 * p5.js Skill — Headless Frame Export
 *
 * Captures frames from a p5.js sketch using Puppeteer (headless Chrome).
 * Uses noLoop() + redraw() for DETERMINISTIC frame-by-frame control.
 *
 * IMPORTANT: Your sketch must call noLoop() in setup() and set
 * window._p5Ready = true when initialized. This script calls redraw()
 * for each frame capture, ensuring exact 1:1 correspondence between
 * frameCount and captured frames.
 *
 * If the sketch does NOT set window._p5Ready, the script falls back to
 * a timed capture mode (less precise, may drop/duplicate frames).
 *
 * Usage:
 *   node export-frames.js sketch.html [options]
 *
 * Options:
 *   --output <dir>    Output directory (default: ./frames)
 *   --width <px>      Canvas width (default: 1920)
 *   --height <px>     Canvas height (default: 1080)
 *   --frames <n>      Number of frames to capture (default: 1)
 *   --fps <n>         Target FPS for timed fallback mode (default: 30)
 *   --wait <ms>       Wait before first capture (default: 2000)
 *   --selector <sel>  Canvas CSS selector (default: canvas)
 *
 * The sketch dir is served on 127.0.0.1 (dotfiles and paths outside it are
 * refused). Chrome sandbox stays on except as root; P5_NO_SANDBOX=1 forces
 * it off, for trusted sketches only.
 *
 * Examples:
 *   node export-frames.js sketch.html --frames 1                     # single PNG
 *   node export-frames.js sketch.html --frames 300 --fps 30          # 10s at 30fps
 *   node export-frames.js sketch.html --width 3840 --height 2160     # 4K still
 *
 * Sketch template for deterministic capture:
 *   function setup() {
 *     createCanvas(1920, 1080);
 *     pixelDensity(1);
 *     noLoop();                    // REQUIRED for deterministic capture
 *     window._p5Ready = true;      // REQUIRED to signal readiness
 *   }
 *   function draw() { ... }
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const http = require('http');

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.csv': 'text/csv',
  '.txt': 'text/plain', '.glsl': 'text/plain', '.frag': 'text/plain', '.vert': 'text/plain',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.otf': 'font/otf', '.ttf': 'font/ttf',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
  '.ogg': 'audio/ogg',
};

// Static server for the sketch dir on loopback: no file:// access flags needed.
function serveDir(root) {
  const realRoot = fs.realpathSync(root);
  const prefix = realRoot.endsWith(path.sep) ? realRoot : realRoot + path.sep;
  const server = http.createServer((req, res) => {
    const notFound = () => { res.writeHead(404); res.end(); };
    let rel, file;
    try { rel = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname); } catch { return notFound(); }
    if (rel.split(/[\\/]/).some(seg => seg.startsWith('.'))) return notFound();
    try { file = fs.realpathSync(path.join(realRoot, rel)); } catch { return notFound(); }
    if (!file.startsWith(prefix) || !fs.statSync(file).isFile()) return notFound();
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(file).on('error', () => res.destroy()).pipe(res);
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

// Parse CLI arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    input: null,
    output: './frames',
    width: 1920,
    height: 1080,
    frames: 1,
    fps: 30,
    wait: 2000,
    selector: 'canvas',
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const val = args[i + 1];
      if (key in opts && val !== undefined) {
        opts[key] = isNaN(Number(val)) ? val : Number(val);
        i++;
      }
    } else if (!opts.input) {
      opts.input = args[i];
    }
  }

  if (!opts.input) {
    console.error('Usage: node export-frames.js <sketch.html> [options]');
    process.exit(1);
  }

  return opts;
}

async function main() {
  const opts = parseArgs();
  const inputPath = path.resolve(opts.input);

  if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
  }

  // Create output directory
  fs.mkdirSync(opts.output, { recursive: true });

  console.log(`Capturing ${opts.frames} frame(s) from ${opts.input}`);
  console.log(`Resolution: ${opts.width}x${opts.height}`);
  console.log(`Output: ${opts.output}/`);

  // Chrome cannot sandbox as root (e.g. in a container); elsewhere keep it on.
  const noSandbox = process.env.P5_NO_SANDBOX === '1' ||
    (typeof process.getuid === 'function' && process.getuid() === 0);
  if (noSandbox) console.log('Chrome sandbox: off (root or P5_NO_SANDBOX=1)');

  const server = await serveDir(path.dirname(inputPath));
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      ...(noSandbox ? ['--no-sandbox', '--disable-setuid-sandbox'] : []),
      '--disable-gpu',
      '--disable-dev-shm-usage',
    ],
  });

  const page = await browser.newPage();

  await page.setViewport({
    width: opts.width,
    height: opts.height,
    deviceScaleFactor: 1,
  });

  // Navigate to sketch over the loopback server
  const sketchUrl = `http://127.0.0.1:${server.address().port}/${encodeURIComponent(path.basename(inputPath))}`;
  await page.goto(sketchUrl, { waitUntil: 'networkidle0', timeout: 30000 });

  // Wait for canvas to appear
  await page.waitForSelector(opts.selector, { timeout: 10000 });

  // Detect capture mode: deterministic (noLoop+redraw) vs timed (fallback)
  let deterministic = false;
  try {
    await page.waitForFunction('window._p5Ready === true', { timeout: 5000 });
    deterministic = true;
    console.log(`Mode: deterministic (noLoop + redraw)`);
  } catch {
    console.log(`Mode: timed fallback (sketch does not set window._p5Ready)`);
    console.log(`  For frame-perfect capture, add noLoop() and window._p5Ready=true to setup()`);
    await new Promise(r => setTimeout(r, opts.wait));
  }

  const startTime = Date.now();

  for (let i = 0; i < opts.frames; i++) {
    if (deterministic) {
      // Advance exactly one frame
      await page.evaluate(() => { redraw(); });
      // Brief settle time for render to complete
      await new Promise(r => setTimeout(r, 20));
    }

    const frameName = `frame-${String(i).padStart(4, '0')}.png`;
    const framePath = path.join(opts.output, frameName);

    // Capture the canvas element
    const canvas = await page.$(opts.selector);
    if (!canvas) {
      console.error('Canvas element not found');
      break;
    }

    await canvas.screenshot({ path: framePath, type: 'png' });

    // Progress
    if (i % 30 === 0 || i === opts.frames - 1) {
      const pct = ((i + 1) / opts.frames * 100).toFixed(1);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      process.stdout.write(`\r  Frame ${i + 1}/${opts.frames} (${pct}%) — ${elapsed}s`);
    }

    // In timed mode, wait between frames
    if (!deterministic && i < opts.frames - 1) {
      await new Promise(r => setTimeout(r, 1000 / opts.fps));
    }
  }

  console.log('\n  Done.');
  await browser.close();
  server.close();
}

main().catch(err => {
  console.error('Error:', err.message);
  if (/sandbox/i.test(err.message)) {
    console.error('Chrome sandbox unavailable. For trusted sketches only: P5_NO_SANDBOX=1 node export-frames.js ...');
  }
  process.exit(1);
});
