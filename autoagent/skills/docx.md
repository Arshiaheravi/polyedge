# Skill: DOCX (Word Documents)

**When to use**: Any task creating or editing .docx files — reports, documentation, spec docs, proposals.

## Create a new document (docx-js)

```bash
npm install -g docx
```

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
        PageNumber, Header, Footer, ExternalHyperlink } = require('docx');
const fs = require('fs');

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter (NOT A4 default)
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } // 1 inch
      }
    },
    children: [ /* content */ ]
  }]
});
Packer.toBuffer(doc).then(buf => fs.writeFileSync('output.docx', buf));
```

## Critical rules

- **Page size**: Always set explicitly — docx-js defaults to A4, not US Letter
- **Never use `\n`** — use separate `Paragraph` elements
- **Never use unicode bullets** (`•`) — use `LevelFormat.BULLET` with numbering config
- **Tables need dual widths**: set `columnWidths` on the table AND `width` on each cell
- **Always `WidthType.DXA`** — never `WidthType.PERCENTAGE` (breaks in Google Docs)
- **`ShadingType.CLEAR`** not SOLID for cell backgrounds
- **`PageBreak` must be inside a `Paragraph`**
- **`ImageRun` requires `type`**: always specify `"png"`, `"jpg"`, etc.
- **Font**: Use Arial (universally supported) as default

## Tables (content width = 9360 DXA for US Letter with 1" margins)

```javascript
new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680], // must sum to table width
  rows: [ new TableRow({ children: [
    new TableCell({
      width: { size: 4680, type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [ new Paragraph({ children: [new TextRun("Cell")] }) ]
    })
  ]})]
})
```

## Validate after creating

```bash
python scripts/office/validate.py output.docx
```

## Edit existing document (unpack → edit XML → repack)

```bash
python scripts/office/unpack.py document.docx unpacked/
# edit XML in unpacked/word/document.xml
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```

## Read content

```bash
pandoc --track-changes=all document.docx -o output.md
```

## StockCards usage
For downloadable Word reports: generate to `/tmp/report.docx`, return as `FileResponse`.
