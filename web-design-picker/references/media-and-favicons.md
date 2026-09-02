# Media and favicon production

## Video inspection

Before embedding a client video:

1. Read duration, dimensions, frame rate, codec, audio, and file size.
2. Inspect frames near the beginning, middle, end, and any important interaction.
3. Identify UI chrome or private information that should be cropped or redacted.
4. Decide whether the video belongs in a hero, proof section, interface viewport, or case study.
5. Avoid autoplay with sound.

## Web video defaults

Use H.264 MP4 as the broad fallback:

- H.264, `yuv420p`;
- `-movflags +faststart`;
- width no larger than needed for the rendered slot;
- 20–30 fps for interface demos;
- no audio unless it adds real information;
- preserve readable UI detail.

Use WebM when it materially reduces size or improves quality. Supply `<source>` elements and a poster image.

Example:

```html
<video muted loop playsinline controls poster="assets/shared/media/demo-poster.jpg">
  <source src="assets/shared/media/demo.webm" type="video/webm">
  <source src="assets/shared/media/demo.mp4" type="video/mp4">
</video>
```

Do not use a large GIF as the primary website format. GIF is a fallback for presentations, email, or tools that cannot play video.

## Poster selection

Choose a frame that:

- clearly demonstrates the claimed capability;
- remains legible at the intended crop;
- does not show a loading state, cursor obstruction, private data, or accidental desktop chrome;
- has enough contrast for any overlaid controls;
- does not imply a different software product than the one shown.

Export at the video’s rendered aspect ratio, usually JPEG quality 82–88 or WebP quality 75–85.

## Optimization command

```bash
python scripts/optimize_video.py input.mp4 PROJECT/design-package/media/web \
  --name software-demo \
  --width 1280 \
  --fps 24 \
  --poster-times 1.5 \
  --gif
```

Use `--crop X:Y:W:H` only after visually checking the crop.

## Favicon principles

A favicon is not a shrunken horizontal logo. Use a simple, high-contrast mark that survives 16–32 px rendering.

Requirements:

- square artboard;
- visible edge clearance;
- no thin typography;
- no dependence on subtle gradients;
- transparent or deliberate background;
- direction-specific treatment;
- ICO fallback plus modern SVG/PNG exports.

## Favicon generation

```bash
python scripts/make_favicons.py source-mark.svg PROJECT/src/assets/brand/direction-a --background transparent
```

The script requires Pillow. SVG input also requires resvg-cli. Inspect 16 px and 32 px results manually; automated resizing cannot fix a mark that is too detailed.
