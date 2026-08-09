---
name: pptx-authoring
description: Guidance for SafeClaw /ppt mode — when and how to call safe_claw_ppt_* tools, Chinese slide design, and [PPT_STEER] iteration. Does NOT replace first-class PPT tools; use tools for structure/save/preview.
---

# PPTX Authoring (guidance only)

## Hard rule

In `/ppt` mode, **structure / save / preview must go through** `safe_claw_ppt_*` tools.
Do not hand-craft `.pptx` via `file_write`. This skill is optional style guidance.

## Tool recipe

1. `safe_claw_ppt_deck_init(deck_id, title, theme_id)`
2. `safe_claw_ppt_slide_upsert` for each page (`slide_index` 1-based; append at `len+1`)
3. Optional: `safe_claw_ppt_theme_apply`, `safe_claw_ppt_image_place`
4. `safe_claw_ppt_save_version` → new `_vN.pptx` (never overwrite)
5. `safe_claw_ppt_preview` → PNG URLs for Deck Preview UI

If deck is `dirty`, preview Fail Fast — save first.

## First reply (unless user says 直接出稿)

```markdown
### Deck Outline
...
### Slide Storyboard
1. Title — bullets — visual intent
### Pending confirmation
- Confirm pages / tone before save
```

## Design norms

- One idea per slide; short titles; ≤6 bullets
- Prefer text shapes over full-page screenshots
- Themes: `default` | `dark` | `warm`
- On `[PPT_STEER] slide=N` or `scope=deck`: precise upsert/theme → save → preview

## Workspace

All outputs under `WORKSPACE_DIR/ppt/` (`~/Downloads/safe_claw_worksapce/workspace/ppt/`).
