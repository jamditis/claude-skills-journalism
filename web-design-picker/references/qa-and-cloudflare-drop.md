# QA and Cloudflare Drop packaging

## Release blockers

Do not package until all of these pass:

- `dist/index.html` exists.
- Every configured direction entry exists.
- Every standalone direction has a title, viewport meta tag, `lang`, and favicon.
- All local `src`, `href`, and `poster` references resolve.
- Every manifest asset and preview resolves.
- Images have `alt` text unless explicitly decorative.
- Form controls have associated labels or accessible names.
- Buttons have a type.
- Videos have usable sources and do not autoplay with sound.
- No archive path is absolute or contains `..`.
- No `.DS_Store`, temporary file, secret, source map, dependency directory, or build cache is included.
- No nested ZIP is included in the deployment archive.
- The deployment archive opens and passes CRC testing.
- `index.html` is the first archive entry and is located at the archive root.

## Visual QA widths

At minimum inspect:

- 390 × 844;
- 768 × 1024;
- 1280 × 800;
- 1440 × 1000.

Check:

- no horizontal overflow;
- no clipped nav, heading, button, form, iframe, or media;
- readable line lengths;
- intentional image and video crops;
- stable section spacing;
- no control bar overlap in the review picker;
- full-screen restoration control remains visible;
- focus state is visible;
- reduced motion does not hide content.

## Static reference rules

Treat these as local and verify them:

- relative paths;
- root-relative paths when the deployment target supports them;
- CSS `url()` references;
- `srcset` entries;
- video `<source>` paths;
- manifest icon paths.

Ignore normal external `https:`, `mailto:`, `tel:`, data URLs, and page fragments, but report them for review.

## Cloudflare Drop archive

The release ZIP should look like this when opened:

```text
index.html
favicon.ico
manifest.webmanifest
robots.txt
concepts/
assets/
design-assets.html
```

It must not look like:

```text
project-name/
  dist/
    index.html
```

or:

```text
index.html
source/
node_modules/
complete-design-assets.zip
```

The builder creates deterministic, cross-platform ZIP metadata, stores already-compressed media without recompressing it, and keeps the deployment handoff separate.

## Size policy

Default hard limit per static file: 25,000,000 bytes. Set a lower project-specific limit when practical.

Recommended targets:

- deployment ZIP below 20 MiB when media permits;
- ordinary images below 500 KiB;
- hero/poster images below 1.5 MiB;
- video sized to actual display need;
- no duplicate MP4/WebM/GIF unless each serves an explicit fallback purpose.

## Local smoke test

Serve `dist` through HTTP, not `file://`:

```bash
python -m http.server 8123 --directory PROJECT_DIR/dist
```

Test:

- direct root load;
- each direction hash;
- each standalone concept URL;
- asset catalog;
- individual download links;
- family ZIP generation;
- all-assets ZIP generation;
- full-screen and restore;
- browser console and network errors.

## Release language

Use precise status terms:

- **built:** files were generated;
- **validated:** automated checks passed;
- **previewed:** screenshots or browser inspection occurred;
- **packaged:** ZIPs were created;
- **deployed:** a host returned a live URL.

Never substitute one status for another.
