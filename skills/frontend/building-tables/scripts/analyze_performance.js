#!/usr/bin/env node

/**
 * Table Data-Operation Benchmark
 *
 * Measures how long client-side table operations take on in-memory rows in
 * Node.js: building row objects, sorting, filtering and paginating. Use it to
 * decide whether a dataset is small enough for client-side sort/filter or
 * should move to server-side operations or virtual scrolling.
 *
 * It does NOT measure DOM rendering, layout or scroll FPS - those need a
 * browser (Chrome DevTools Performance panel, React Profiler, Lighthouse).
 * Browser JavaScript is usually somewhat slower than these Node numbers,
 * especially on low-end devices, so treat results as a lower bound.
 *
 * Usage:
 *   node analyze_performance.js                       # 100, 1000, 10000 rows
 *   node analyze_performance.js --rows 10000          # one size
 *   node analyze_performance.js --rows=1000,50000 --columns=20
 *   node analyze_performance.js --json                # machine-readable output
 */

const { performance } = require('perf_hooks');

// Budgets for an operation to feel instant in the UI (blocking the main thread)
const INSTANT_MS = 50;
const ACCEPTABLE_MS = 200;

class TablePerformanceAnalyzer {
  constructor({ columnCount = 10 } = {}) {
    this.columnCount = columnCount;
    this.results = [];
  }

  createRows(rowCount) {
    const departments = ['Engineering', 'Sales', 'Support', 'Finance', 'Legal'];
    const rows = new Array(rowCount);
    for (let i = 0; i < rowCount; i++) {
      const row = { id: i, name: `User ${(i * 7919) % rowCount}`, dept: departments[i % 5], amount: (i * 2654435761) % 100000 };
      for (let c = 4; c < this.columnCount; c++) row[`col${c}`] = `v${(i + c) % 997}`;
      rows[i] = row;
    }
    return rows;
  }

  time(fn, repeats = 5) {
    // Median of several runs to dampen JIT warm-up and GC noise
    const samples = [];
    let result;
    for (let r = 0; r < repeats; r++) {
      const start = performance.now();
      result = fn();
      samples.push(performance.now() - start);
    }
    samples.sort((a, b) => a - b);
    return { ms: samples[Math.floor(samples.length / 2)], result };
  }

  benchmark(rowCount) {
    const build = this.time(() => this.createRows(rowCount), 3);
    const rows = build.result;
    const collator = new Intl.Collator(undefined, { numeric: true });

    const sortNumeric = this.time(() => rows.slice().sort((a, b) => a.amount - b.amount));
    const sortString = this.time(() => rows.slice().sort((a, b) => collator.compare(a.name, b.name)));
    const filter = this.time(() => rows.filter(r => r.dept === 'Sales' && r.name.includes('1')));
    const search = this.time(() => {
      const q = 'user 12';
      return rows.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
    });
    const page = this.time(() => rows.slice(rowCount / 2, rowCount / 2 + 50));

    const result = {
      rows: rowCount,
      columns: this.columnCount,
      buildMs: build.ms,
      sortNumericMs: sortNumeric.ms,
      sortStringMs: sortString.ms,
      filterMs: filter.ms,
      globalSearchMs: search.ms,
      pageSliceMs: page.ms,
      heapUsedMB: process.memoryUsage().heapUsed / 1024 / 1024,
    };
    result.recommendation = this.recommend(result);
    this.results.push(result);
    return result;
  }

  recommend(r) {
    const worst = Math.max(r.sortStringMs, r.globalSearchMs);
    if (worst <= INSTANT_MS) return 'client-side sort/filter is fine';
    if (worst <= ACCEPTABLE_MS) return 'client-side works but debounce search and memoize sorted rows; consider a Web Worker';
    return 'move sort/filter/search to the server (or a Worker) and paginate or virtualize rendering';
  }

  printReport() {
    const fmt = ms => `${ms.toFixed(2)}ms`;
    console.log('\nTable data-operation benchmark (Node.js, median of runs; excludes DOM rendering)\n');
    for (const r of this.results) {
      console.log(`${r.rows} rows x ${r.columns} columns`);
      console.log(`  build rows      ${fmt(r.buildMs)}`);
      console.log(`  sort (number)   ${fmt(r.sortNumericMs)}`);
      console.log(`  sort (string)   ${fmt(r.sortStringMs)}`);
      console.log(`  filter          ${fmt(r.filterMs)}`);
      console.log(`  global search   ${fmt(r.globalSearchMs)}`);
      console.log(`  page slice      ${fmt(r.pageSliceMs)}`);
      console.log(`  heap used       ${r.heapUsedMB.toFixed(1)} MB`);
      console.log(`  => ${r.recommendation}\n`);
    }
    console.log(`Budgets: <=${INSTANT_MS}ms feels instant, <=${ACCEPTABLE_MS}ms acceptable with feedback.`);
    console.log('Measure rendering and scrolling separately in the browser (DevTools Performance panel).');
  }
}

function parseArgs(argv) {
  const opts = { rowCounts: [100, 1000, 10000], columnCount: 10, json: false };
  const takeValue = (i, name) => {
    const arg = argv[i];
    if (arg.includes('=')) return [arg.split('=')[1], i];
    if (i + 1 >= argv.length) throw new Error(`${name} needs a value`);
    return [argv[i + 1], i + 1];
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      opts.help = true;
    } else if (arg === '--json') {
      opts.json = true;
    } else if (arg.startsWith('--rows')) {
      const [value, next] = takeValue(i, '--rows');
      opts.rowCounts = value.split(',').map(Number);
      i = next;
    } else if (arg.startsWith('--columns')) {
      const [value, next] = takeValue(i, '--columns');
      opts.columnCount = Number(value);
      i = next;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  if (opts.rowCounts.some(n => !Number.isInteger(n) || n <= 0)) throw new Error('--rows must be positive integers');
  if (!Number.isInteger(opts.columnCount) || opts.columnCount < 4) throw new Error('--columns must be an integer >= 4');
  return opts;
}

if (require.main === module) {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(2);
  }
  if (opts.help) {
    console.log('Usage: node analyze_performance.js [--rows N[,N...]] [--columns N] [--json]');
    console.log('Benchmarks in-memory sort/filter/search/pagination; does not measure DOM rendering.');
    process.exit(0);
  }
  const analyzer = new TablePerformanceAnalyzer({ columnCount: opts.columnCount });
  for (const n of opts.rowCounts) analyzer.benchmark(n);
  if (opts.json) console.log(JSON.stringify(analyzer.results, null, 2));
  else analyzer.printReport();
}

module.exports = TablePerformanceAnalyzer;
