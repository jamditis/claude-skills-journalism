# Troubleshooting

## Host says “Something went wrong”

Check in this order:

1. Is `index.html` at ZIP root?
2. Is there an unnecessary enclosing directory?
3. Does the ZIP contain another large ZIP?
4. Are there symlinks, absolute paths, or path traversal entries?
5. Are filenames using unusual characters?
6. Is an individual file unusually large?
7. Does the archive pass CRC/integrity testing?
8. Does the extracted site work through a local HTTP server?
9. Do all HTML references remain inside the extracted root?

Repackage from a clean staging directory rather than modifying the failed ZIP in place.

## Picker shows a blank frame

- open the standalone concept URL directly
- inspect the iframe `src`
- verify filename case
- use a local HTTP server rather than `file://`
- check whether a restrictive Content Security Policy blocks framing
- verify the concept does not redirect to an external origin

## Videos do not autoplay

- ensure `muted` and `playsinline` are present
- provide a poster so the page still communicates the idea
- do not depend on autoplay for essential information
- test whether the browser blocks autoplay because audio remains

## Download link does nothing

- confirm the file exists at the resolved relative path
- avoid links to container or conversation-only locations
- use actual files rather than data URLs for large downloads
- verify the host serves the file type

## Favicon is missing

- provide SVG and ICO fallbacks
- make paths relative to each page depth
- include a root `/favicon.ico` only when the host root is stable
- clear browser cache during testing
- verify small-size legibility

## Three directions look too similar

Return to the distinctness matrix. Change page architecture and content emphasis before changing decorative details. Different typography or color is not enough.

## Site looks generic

Remove decorative conventions, then rebuild around the strongest evidence, the client’s actual working materials, and a specific organizing metaphor.
