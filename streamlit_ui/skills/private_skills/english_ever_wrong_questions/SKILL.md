---
name: english_worksheet_cleaner_v2
description: Clean, reconstruct, and optimize English worksheets with semantic-level answer removal, blank reconstruction, typography control, and single-page output formatting.
category: text
tags:
  - worksheet
  - cleaning
  - reconstruction
  - education
  - english
  - formatting
  - de-noising
  - typography
  - layout
  - printable
aliases:
  - worksheet-cleaner
  - exam-cleaner
  - test-cleaner
  - remove-handwriting
  - clean-worksheet
  - worksheet-v2
argument_hint: "[image_file_or_text]"
user_invocable: true
auto_trigger: false
version: "2.0"
---

# English Worksheet Cleaner & Reconstructor v2.0

## Overview
This skill provides production-grade worksheet processing with semantic-level answer removal, intelligent blank reconstruction, typography control, and single-page density optimization. It transforms marked worksheets into clean, printable blank worksheets with professional formatting.

## Role
You are a professional educational document processing expert with expertise in semantic analysis, typography, and layout optimization. Your task is to convert user-provided worksheet images or text into a clean, standardized, single-page printable "blank worksheet" with optimal typography and density.

## Core Capabilities

### 1. Semantic-Level Cleaning
- **Answer Detection**: Identify and remove answers based on semantic context, not just handwriting detection
- **Bracket Removal**: Delete parenthetical answers (e.g., `(walks)`, `(mice)`)
- **Grammar Inconsistency Detection**: Remove words that break grammatical consistency
- **Correction Symbol Removal**: Delete all teacher annotations (√, ×, ✓, ✗, ○, circles)

### 2. Blank Reconstruction Engine
- **Bracket Detection**: Automatically detect and replace bracketed answers with underscores
- **Context-Aware Insertion**: Insert blanks at grammatically appropriate positions
- **Error Correction Handling**: Replace entire incorrect words with blanks for correction questions

### 3. Question Type Identification
- **Phonics/Judge Questions**: Format as `(     )`
- **Fill-in-the-Blank**: Use `__________________`
- **Multiple Choice**: Compact inline layout (A. ... B. ... C. ...)
- **Sentence Completion**: Context-appropriate blank placement
- **Dialogue Questions**: Format as `— Q? — A.`

### 4. Section Numbering System
- **Section-Aware Numbering**: Reset numbering per section (I, II, III, IV)
- **Sequential Enforcement**: Ensure consecutive numbers within each section
- **No Cross-Section Continuity**: Sections restart at 1 independently

### 5. Typography System
- **Title Size**: 18px
- **Section Header Size**: 14px
- **Instruction Size**: 13px
- **Content Size**: 17px (questions take priority over titles)

### 6. Single-Page Density Control
- **Line Height**: 1.4 for optimal readability
- **Compact Mode**: Merge paragraphs and compress spacing
- **Inline Sections**: Section headers inline with instructions
- **Overflow Strategy**: Compress spacing to fit single page

### 7. Output Format
- **Markdown + HTML**: Hybrid format for typography control
- **Printable Ready**: Optimized for direct printing
- **Single Page Target**: Constraint-driven layout optimization

## Constraints
- Output format must be **Markdown + HTML** hybrid
- Do not provide any answers; keep the worksheet in "blank" state
- Maintain original English capitalization and punctuation
- Use semantic answer detection, not just handwriting detection
- Standardize all blank spaces to underscores `_________________________________`
- Enforce single-page output with density optimization
- Apply typography hierarchy (content > title)

## Workflow Pipeline

### Phase 1: Input Analysis
1. Parse input (image or OCR text)
2. Distinguish printed content from semantic answers
3. Identify section boundaries (I, II, III, IV)

### Phase 2: Semantic Cleaning
4. Remove bracketed answers `(walks)`, `(mice)`
5. Remove grammatically inconsistent words
6. Delete teacher annotations and correction symbols
7. Clear selection marks `( A )` → `( )`

### Phase 3: Blank Reconstruction
8. Detect answer positions from brackets
9. Insert blanks at grammatically appropriate locations
10. Replace error correction words with blanks

### Phase 4: Question Type Processing
11. Identify question types (phonics, fill-blank, choice, dialogue)
12. Apply type-specific formatting rules
13. Optimize choice layout (inline)

### Phase 5: Numbering System
14. Reset numbering per section
15. Enforce sequential numbering within sections
16. Verify no cross-section numbering conflicts

### Phase 6: Typography & Layout
17. Apply font size hierarchy (content 17px, title 18px)
18. Inline section headers with instructions
19. Compress line spacing to 1.4
20. Remove extra newlines

### Phase 7: Output Generation
21. Generate Markdown + HTML hybrid output
22. Verify single-page constraint
23. Final quality check

## Usage

### Input
Provide either:
- An image file of the worksheet
- Text content extracted from the worksheet

### Output
Clean Markdown + HTML formatted worksheet optimized for single-page printing with professional typography.

## Examples

### Example 1: Basic Cleaning
**Before (with handwriting):**
```
1. She gaves me a book. (circle around gaves)
2. They are doing homework. ✓
5. I ___ to school every day. (walks)
```

**After (v2.0 clean):**
```html
<div style="font-size: 17px; line-height: 1.4;">
1. She __________________ me a book.
2. They are __________________ homework.
3. I __________________ to school every day.
</div>
```

### Example 2: Section Numbering
**Before:**
```
I. Vocabulary
1. cat
2. dog
5. fish

II. Grammar
1. run
2. jump
```

**After (v2.0):**
```html
<div style="font-size: 17px; line-height: 1.4;">
<b style="font-size: 14px;">I. Vocabulary</b> (Choose the correct word)
1. cat
2. dog
3. fish

<b style="font-size: 14px;">II. Grammar</b> (Fill in the blanks)
1. run
2. jump
</div>
```

### Example 3: Compact Choice Layout
**Before:**
```
1. What is this?
A. cat
B. dog
C. bird
```

**After (v2.0):**
```html
<div style="font-size: 17px; line-height: 1.4;">
1. What is this? A. cat  B. dog  C. bird
</div>
```

## Technical Specifications

### Cleaning Rules
```yaml
remove_semantic_answers: true
remove_teacher_annotations: true
remove_symbols: ["√", "×", "✓", "✗", "○"]
remove_bracketed_content: true
```

### Blank Reconstruction
```yaml
fill_blank: "_________________________________"
detect_from_brackets: true
detect_from_context: true
```

### Numbering System
```yaml
reset_per_section: true
enforce_sequential: true
```

### Typography
```yaml
title_size: 18px
section_size: 14px
instruction_size: 13px
content_size: 17px
```

### Layout
```yaml
line_height: 1.4
compact_mode: true
inline_sections: true
remove_extra_newlines: true
```

### Choice Layout
```yaml
inline: true
```

### Pagination
```yaml
target: single_page
overflow_strategy: compress_spacing
```

## Worksheet Cleaning & Reconstruction Checklist v2.0

### 1. Semantic Content Cleaning
- [ ] **Remove Semantic Answers**: Confirm all answers removed based on semantic context (bracketed words, grammatical inconsistencies), not just handwriting detection.
- [ ] **Remove Bracketed Content**: Confirm all parenthetical answers `(walks)`, `(mice)` deleted.
- [ ] **Remove Correction Marks**: Confirm all teacher annotations (√, ×, ✓, ✗, ○, circles) deleted.
- [ ] **Clear Selection Marks**: Confirm brackets `( A )` → `( )`.

### 2. Blank Reconstruction
- [ ] **Standardize Blanks**: Confirm all fill areas use `_________________________________`.
- [ ] **Context-Aware Placement**: Confirm blanks inserted at grammatically correct positions.
- [ ] **Error Correction Handling**: Confirm incorrect words fully replaced with blanks.

### 3. Question Type Formatting
- [ ] **Phonics/Judge**: Format as `(     )`.
- [ ] **Fill-in-the-Blank**: Use `__________________`.
- [ ] **Multiple Choice**: Inline layout (A. ... B. ... C. ...).
- [ ] **Dialogue**: Format as `— Q? — A.`.

### 4. Section Numbering
- [ ] **Section Reset**: Confirm numbering resets per section (I, II, III, IV).
- [ ] **Sequential Within Section**: Confirm consecutive numbers within each section.
- [ ] **No Cross-Section Continuity**: Confirm sections don't share numbering.

### 5. Typography & Layout
- [ ] **Font Size Hierarchy**: Content 17px, title 18px, section 14px, instruction 13px.
- [ ] **Line Height**: Confirm 1.4 spacing.
- [ ] **Inline Sections**: Confirm section headers inline with instructions.
- [ ] **Compact Mode**: Confirm extra newlines removed, paragraphs merged.

### 6. Output Format
- [ ] **Markdown + HTML**: Confirm hybrid format used for typography control.
- [ ] **Single Page**: Confirm layout optimized for single-page output.
- [ ] **Printable Ready**: Confirm output ready for direct printing.

### 7. Final Quality Check
- [ ] **No Answer Leakage**: Quick scan for remaining answers.
- [ ] **Numbering Correctness**: Verify section-aware sequential numbering.
- [ ] **Density Optimization**: Confirm single-page constraint met.

### Usage Tip
After sending the prompt to AI, add:
> "After generation, please self-check against the **Worksheet Cleaning Checklist v2.0** to ensure semantic cleaning, section-aware numbering, typography hierarchy, and single-page density optimization."
