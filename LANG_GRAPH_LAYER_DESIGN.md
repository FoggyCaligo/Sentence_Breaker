# LANG_GRAPH Layer Design

## Goal

This document defines the next `LANG_GRAPH` design for `Sentence_Breaker`.

The goal is not:

- counting raw substring frequency across all stored history
- re-reading whole sentence strings at runtime
- relying on a manually patched dictionary

The goal is:

- store each input sentence as its own vertical layer
- store only graph-like transition elements inside each character cell
- when a new sentence arrives, keep only the stored sentence layers that match the current path
- judge word-like bundles by how many matching layers remain visible from above

This is the "cellophane overlap" model described in the project discussion.

---

## Core Picture

Think of the structure like a 3D layered board.

- floor axis:
  character cells (`alph`)
- height axis:
  one layer per input sentence
- inside each cell:
  small transition elements

Each transition element stores:

1. the address of the next character cell
2. the `sentence_id`
3. optionally the position inside that sentence

So the system does not need to store the original sentence string as a full text row.
It only stores the path fragments that make up each sentence layer.

---

## Main Idea

When a new sentence is processed:

1. follow the current sentence one step at a time
2. at each step, keep only stored elements whose next address matches the current next character
3. drop every `sentence_id` that diverges at that point
4. after filtering, look from top to bottom
5. count how many valid elements still cover each region

The more surviving layers overlap on a region, the more that region behaves like a word.

This means:

- `엄마` can stand out
- `엄청` will not incorrectly reinforce `엄마`
- unrelated branches are removed by path agreement, not by guesswork

---

## Data Model

### 1. `alph_nodes`

One row per character cell.

Suggested fields:

- `alph TEXT PRIMARY KEY`
- `created_at TEXT`

Meaning:

- a floor cell on the board

### 2. `sentence_layers`

One row per input sentence layer.

Suggested fields:

- `sentence_id TEXT PRIMARY KEY`
- `char_length INTEGER NOT NULL`
- `created_at TEXT`

Meaning:

- one vertical layer
- enough metadata to know how long the layer is

### 3. `alph_links`

One row per transition element stored inside a character cell.

Suggested fields:

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `source_alph TEXT NOT NULL`
- `target_alph TEXT NOT NULL`
- `sentence_id TEXT NOT NULL`
- `position INTEGER NOT NULL`
- `created_at TEXT`

Recommended indexes:

- `(source_alph, target_alph)`
- `(sentence_id, position)`
- `(source_alph, sentence_id)`

Meaning:

- from this character cell, this sentence layer moved to that next character cell at this position

This is the real "stack of elements in a cell".

### Optional 4. `bundle_memory`

This is optional, but useful if the rule is:
"once a bundle is introduced as a word, later inputs may treat it as a learned unit."

Suggested fields:

- `bundle_text TEXT PRIMARY KEY`
- `first_sentence_id TEXT NOT NULL`
- `mention_count INTEGER NOT NULL DEFAULT 1`
- `created_at TEXT`
- `updated_at TEXT`

Meaning:

- explicit learned bundles, separate from raw sentence-layer filtering

This table is not the base graph.
It is a memory of bundles discovered or declared.

---

## Ingestion Algorithm

Input:

- raw text

Output:

- one new `sentence_id`
- one new vertical layer in storage

Steps:

1. split the input into `alph` units
   - include spaces
   - include punctuation
2. create `sentence_id`
3. insert the `sentence_id` into `sentence_layers`
4. ensure every `alph` exists in `alph_nodes`
5. for each adjacent pair:
   - insert one `alph_links` row
   - store:
     - `source_alph`
     - `target_alph`
     - `sentence_id`
     - `position`

Important rule:

- even if the same transition already exists, do not reuse it
- a new sentence creates a new set of transition elements

This preserves the vertical-layer idea.

---

## Runtime Filtering Algorithm

Input:

- current sentence to segment

Output:

- surviving layer coverage map
- candidate bundles

### Stage 1. Build the current path

Split the current input into:

- `alph[0], alph[1], alph[2], ...`

### Stage 2. Collect local candidates per step

For each step `i -> i+1`:

- query `alph_links` where:
  - `source_alph == alph[i]`
  - `target_alph == alph[i+1]`

This gives the set of layer elements that match the current sentence at that step.

Represent this as:

- `step_matches[i] = set[(sentence_id, position)]`

or at minimum:

- `step_sentence_ids[i] = set[sentence_id]`

### Stage 3. Keep only path-consistent layers

The important part is not just "same pair exists".
The same sentence layer must continue consistently.

For a sentence layer to survive from step `i` to step `i+1`:

- the same `sentence_id` must appear in both steps
- and its positions must advance correctly
  - if step `i` uses `position = p`
  - then step `i+1` must use `position = p + 1`

So the real survivor state should be:

- `(sentence_id, start_position)`

or:

- `(sentence_id, current_position)`

This is what removes unrelated branches.

### Stage 4. Form surviving spans

After chaining the valid layer states across the input:

- every surviving state marks one visible path segment
- if many states cover the same range, that range is strong

Now we can build a coverage map:

- `coverage[start][end] = number of surviving layer states`

or simpler:

- for every possible span in the current input, count how many surviving layers support it

This count is the "visible stacked cell count" view from above.

---

## Segment Selection Rule

The final result should not use only raw count.

If we use only count:

- short spans may dominate unfairly
- single characters may always look strong

So each candidate span should be ranked by at least:

1. surviving layer count
2. span length
3. boundary consistency

### Suggested score

For a candidate span:

- `support_count`
- `span_length`
- `boundary_score`

Possible simple scoring:

`score = support_count * span_length`

Then break ties by:

1. larger `span_length`
2. stronger boundary score
3. fewer total pieces in the final segmentation

### Boundary consistency

This checks whether the same span tends to begin and end together across surviving layers.

This matters because:

- `엄마` may be stronger than `엄`
- `엄마가` may or may not be stronger depending on real layer support

Boundary consistency helps distinguish:

- a true learned bundle
- a substring that merely appears inside longer bundles

---

## Single-Character Policy

The project discussion suggests:

- single characters may exist in the graph
- but they should not dominate if stronger bundles exist

Recommended policy:

- allow single-character fallback only when no supported multi-character span wins
- never let single characters outrank a supported longer span on count alone

This keeps the system from collapsing into character-by-character output too easily.

---

## Explicit Learned Bundle Rule

The project also states:

- if a bundle is introduced once as a word, later inputs may treat it as a word from then on

This can be implemented in one of two ways.

### Option A. Pure layer effect

If a word was entered once by itself:

- that one sentence layer already exists
- future matching can rediscover it through the normal layer filter

Pros:

- simplest
- stays close to the base graph philosophy

Cons:

- "declared word" and "accidentally seen once" are not distinguished

### Option B. Separate bundle memory

When a word is entered explicitly:

- store it in `bundle_memory`
- let runtime treat it as a preferred candidate

Pros:

- matches the rule more directly
- lets explicit word teaching behave differently from accidental appearance

Cons:

- adds another memory layer

Recommendation:

- keep Option A as the base
- allow Option B later if the project wants explicit teaching behavior

---

## Performance Direction

The current substring-count implementation becomes slower because it:

- enumerates many substrings
- scans historical transitions repeatedly

The layer-filter model can be faster if runtime is organized around:

- direct `(source_alph, target_alph)` lookup
- chaining matching `sentence_id + position`
- counting surviving states only

This means runtime work is proportional more to:

- the length of the current sentence
- the number of locally matching links

and less to:

- all possible substrings across all history

### Future optimization

If needed, add cached aggregate tables such as:

- `pair_weight(source_alph, target_alph, count)`
- `span_cache(...)`

But these should be helpers.
The main truth should remain the sentence-layer filter model.

---

## Why This Design Fits the Project Better

This model matches the original intent better than plain substring frequency.

Because it:

- keeps sentence history as layers
- stores only path elements, not full raw sentence copies
- filters by current-path agreement
- lets bundles emerge by surviving overlap

So this design preserves the key metaphor:

"Look only at the layers that still align with the current sentence, and count what remains visible from above."

---

## Suggested Next Implementation Steps

1. replace `seq_edges` with `sentence_layers + alph_links`
2. remove substring-count scoring from runtime
3. implement step-by-step layer survivor chaining
4. build span coverage counts from surviving layer states
5. add a segment chooser based on:
   - support count
   - span length
   - boundary consistency
6. later, optionally add `bundle_memory`

---

## One-Line Summary

`Sentence_Breaker` should move from "substring frequency search" to "sentence-layer filtering and visible overlap counting".
