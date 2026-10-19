# ADR Tooling and Site Integration

This file covers only the tooling around Architecture Decision Records: CLI helpers and publishing ADRs in a documentation site. For when to write an ADR, its template, location and numbering, use the **documentation-and-adrs** skill, and follow the repository's existing ADR convention (directory, format, numbering) when one exists. The paths below use `docs/adr`; substitute the repository's directory.

## Tools

### adr-tools

Command-line tool for managing ADRs (it uses its own Nygard-style template unless configured):

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
