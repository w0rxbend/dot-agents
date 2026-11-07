# ADR Tooling and Site Integration

Covers only tooling around Architecture Decision Records: CLI helpers and publishing ADRs in documentation site. For when to write ADR, its template, location and numbering, use **documentation-and-adrs** skill. Follow repository's existing ADR convention (directory, format, numbering) when one exists. Paths below use `docs/adr`; substitute repository's directory.

## Tools

### adr-tools

Command-line tool for managing ADRs. Uses own Nygard-style template unless configured:

```bash
# Install
brew install adr-tools

# Initialize ADR directory
adr init docs/adr

# Create new ADR
adr new "Use PostgreSQL for primary database"

# Create ADR that supersedes another
adr new -s 1 "Migrate to MongoDB"

# Generate table of contents
adr generate toc > docs/adr/README.md
```

### log4brains

Documentation site with ADR support:

```bash
# Install
npm install -g log4brains

# Initialize
log4brains init

# Preview
log4brains preview

# Build
log4brains build
```

## Integration with Documentation Sites

### Docusaurus Integration

```javascript
// docusaurus.config.js
module.exports = {
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          path: 'docs',
          sidebarPath: require.resolve('./sidebars.js'),
        },
      },
    ],
  ],
};

// sidebars.js
module.exports = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Architecture Decisions',
      items: [
        'adr/0001-database-selection',
        'adr/0002-microservices',
      ],
    },
  ],
};
```

### MkDocs Integration

```yaml
# mkdocs.yml
nav:
  - Home: index.md
  - Architecture Decisions:
    - ADR-0001 Database Selection: adr/0001-database-selection.md
    - ADR-0002 Microservices: adr/0002-microservices.md
```
