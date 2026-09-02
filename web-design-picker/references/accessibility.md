# Accessibility baseline

The design picker is a prototype, but it should not normalize inaccessible patterns.

## Required on every page

- `<html lang>`
- descriptive `<title>`
- viewport meta tag
- one clear page-level heading
- semantic landmarks
- visible keyboard focus
- labels for form controls
- useful image alternative text
- captions or surrounding explanation for product media when needed
- sufficient text contrast
- controls that remain usable at 200% zoom
- `prefers-reduced-motion` handling

## Picker-specific requirements

- tablist/tab roles and `aria-selected`
- `aria-controls` matching iframe IDs
- descriptive iframe titles
- live-region announcement when the selected direction changes
- keyboard switching with focus management
- visible way to exit presentation mode
- actions that do not rely only on color

## Mobile requirements

- no horizontal page overflow at 390 px
- touch targets generally at least 44 CSS px in one dimension
- no critical text below a readable size
- no interaction available only on hover
- no fixed control that covers important content

## Forms

- labels must remain visible; placeholders are not labels
- errors must be textual, not color-only
- do not claim successful submission without a backend response
- local prototype actions must explain what occurred

## Motion

Do not rely on scroll reveal to expose essential content. Under reduced motion, stop autoplay where appropriate and remove nonessential transitions.
