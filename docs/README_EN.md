# Audion Office Image Optimizer

[Русский](README_RU.md) · [User Guide](USER_GUIDE_EN.md)

Processes raster images **inside** Word documents and PowerPoint presentations,
without taking the document apart.

## Why It Exists

A document with photographs weighs a hundred megabytes because every image inside
it is a phone picture at full resolution. It opens slowly, will not go by email,
and behaves unpredictably in print.

The usual approach is to extract the images, process them, and put them back. That
approach loses everything: position, text wrapping, captions, anchoring to the
paragraph.

This program works on the images **in place**: the document stays the same
document, and only what is inside the pictures changes.

## Principles

**The layout is untouched.** Position, size on the page, wrapping, anchoring — all
stay as they were. Pixels change, markup does not.

**The colour profile is chosen explicitly.** As in the other Audion programs: one
thing for screen, another for print, and a person decides which.

**The source is not modified.** The result is written separately.

## Next

* [User Guide](USER_GUIDE_EN.md) — step by step.

---

## Technical Reference

### Layout

```
system_core\app\   the code
runtime\           embedded Python
config\            defaults and colour profiles
```

### Workbench Naming

One shared vocabulary across all Audion projects: **Source**, **Add file…**,
**Target**, **Reset**, **Delete**, **List**.
