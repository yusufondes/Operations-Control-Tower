# HALY business portfolio presentation

## Deliverables

- `../docs/portfolio/HALY-Operations-Control-Tower-Case-Study-Revised.pptx`: 14-slide,
  English, editable business presentation with speaker notes and source citations.
- `../docs/portfolio/HALY-Operations-Control-Tower-Case-Study-Revised.pdf`: visually
  matched, image-based sharing copy. It is not a searchable-text or accessible
  tagged-PDF equivalent; use the PowerPoint for editing and speaker notes.

Use the Revised pair for sharing. The earlier 17-slide pair remains unchanged
in the explicitly labelled [historical archive](../docs/portfolio/archive/README.md)
for recovery and comparison. Its old access/CI notes are historical. The revision removes
repeated explanations and shortens visible wording while retaining all seven
evidence screenshots and detailed limitations in speaker notes.

The story explains the campaign stock gap, accepted dispatch dates, date-first
allocation, complete individual shipments, corporate backorders, own manufacture,
owned exceptions, demonstrated outcomes and project contributions. Technology is
last. All HALY data is fictional/synthetic. No real-client results, measured ROI,
production deployment or full campaign coverage in remote CI are claimed. The
last slide links to the source repository on GitHub. Its README and Actions page
provide current build status. The recorded 81 local test methods and 11 campaign
probe cases passed on 2026-10-15; they are separate from the eight base-addon
test methods configured in GitHub CI.

## Source and design

Authoring source is `build_haly_portfolio.mjs`, using the Codex-bundled
`@oai/artifact-tool`. Text, two tables and the repository hyperlink are native
PowerPoint elements. Seven unchanged evidence screenshots come from
`../docs/evidence/task-0007/`; their crops highlight the relevant business fields.
The browser examples are separate from the complete 900-unit runtime scenario.
Speaker notes identify evidence and limitations for each slide.

Design: 16:9, Arial, restrained navy/ivory/teal palette, generous whitespace,
short headings and simple business language. The revised accent is darker teal
`#096A6E` on ivory `#F6F8F5` for stronger text contrast. Primary research references:

- [Microsoft: Effective presentations](https://support.microsoft.com/en-us/powerpoint/tips-for-creating-and-delivering-an-effective-presentation)
- [Microsoft: Combining colors](https://support.microsoft.com/en-us/powerpoint/combining-colors-in-powerpoint-mistakes-to-avoid)

These sources informed readability and contrast, not project capability claims.

## Representative cover image

Asset: `../docs/portfolio/assets/haly-cover-concept.png`.
Generated on 2026-10-15 with the built-in image-generation tool, opaque background,
no reference images. It is a representative concept, not a real HALY photograph.
The fictional/synthetic scope is visible on the cover and in its notes.

Exact generation prompt:

> Use case: product-mockup. Asset type: premium editorial cover photograph for an English business portfolio presentation about a fictional powdered-drink manufacturer managing holiday campaign orders. Create a polished wide 16:9 corporate still-life: two unbranded matte off-white powdered-drink pouches, one stainless steel powder scoop with pale powder, neatly stacked kraft shipping cartons and subtle warehouse shelving softly blurred in the distant background. Subject grouped on the RIGHT two thirds, visually spacious and quiet LEFT third. Sophisticated restrained navy blue, warm ivory and muted teal palette. Soft directional studio daylight, beautiful realistic paper and steel textures, architectural composition, no people. No text, no logos, no numbers, no watermark, no Christmas ornaments. This is a representative concept image, not evidence of an actual company or facility. Landscape composition suitable for a 16:9 PowerPoint cover; do not draw a slide, charts, text or UI.

## Rebuilding in the authoring environment

No application dependency, ERP installation or service change is required.
The scripts target the verified local repository path. The bundled runtime and
skill paths in the builder are authoring-environment paths, not portable project
dependencies. Adapt those paths when using another machine; do not install new
tools or alter the ERP environment merely to reproduce the deck.

1. Use the presentation skill and its required create/edit operation marker.
2. Copy the builder to a private build directory with access to the bundled
   `@oai/artifact-tool` module. Keep build caches/renders out of this repository.
3. Set `RUNTIME_NODE_MODULES` to the bundled node_modules directory, optionally
   `HALY_DECK_WORKSPACE` to that private workspace and `HALY_DECK_FILENAME` to a
   fresh filename. Run the builder with bundled Node. Its finalizer refuses to
   overwrite the final output and checks package/layout/font/table arithmetic
   and first-party reimport. Inspect every rendered slide as well.
4. For a sharing PDF, use the PDF skill operation marker once. Copy
   `export_haly_pdf.mjs` and `export_haly_pdf.py` together to the private build
   directory. Set `HALY_PYTHON` to bundled Python with ReportLab and run:

   `node export_haly_pdf.mjs INPUT.pptx OUTPUT.pdf PRIVATE_RENDER_DIR`

   This imports the finalized PPTX, renders 14 pages at 1920x1080 and places those
   exact renders into a 16:9 PDF. It refuses an existing PDF and retains the last
   slide's GitHub link. The image-based fallback avoids an unavailable bundled
   `#standard-fonts/Helvetica` dependency in native PDF export; no installation
   or library patch was performed.
5. Render the PDF with Poppler and inspect all pages. Copy only validated final
   deliverables and intentional source assets into the repository.

Validation evidence and output hashes are recorded in `../docs/TASKS.md`,
TASK-0009 and TASK-0012. Automated import/render checks are not native Microsoft PowerPoint
execution or a complete accessibility audit. Owner acceptance remains required.
