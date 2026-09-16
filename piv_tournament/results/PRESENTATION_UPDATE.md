# Presentation update — only newly executed material from the latest pass

## New slide 1 — Raw-byte PIVlab forensic freeze now has distributed field evidence

**On slide**

- Complete raw bytes SHA-256 frozen for **13 stratified exports**: 0001, 0002, every ~25 fields, 0249, 0250.
- Every tested file: **3,850 rows = 70 × 55 grid**.
- Every tested file: **1,192 finite active vectors + 2,658 masked/type-0 nodes**.
- Coordinate grid and static mask are identical across the 13 raw files.
- Pair provenance and calibration metadata are correct at every tested location.
- Direct/type-1 fraction varies **49.92%–62.08%** of active vectors.

**Visual:** one compact timeline from export 0001 to 0250 with the 13 hashed checkpoints, plus a two-column box: `70×55 = 3850` and `1192 active / 2658 masked`.

**Say:** “This is no longer a header-only continuity argument. I downloaded complete raw PIVlab files distributed across the historical window, hashed the full bytes, and parsed every vector row. The fixed 1,192-cell active domain used in the tournament is directly visible in every tested raw export.”

**Do not claim:** the complete 250-file cryptographic freeze is finished. It is now automated for Colab but still must be executed.

## New slide 2 — Grid contradiction strengthened with full-lattice statistics

**On slide**

- Stored calibration: **0.00019061 m/px**.
- Robust median lattice pitch from complete raw grids: **0.00343104452 m**.
- Physical grid step: **18.00033849 px ≈ 18 px**.
- Simple 18 px final window + 50% overlap would imply **9 px**.
- First-pass setting: **INSUFFICIENT_EVIDENCE**.

**Say:** “The earlier value came from a single coordinate difference. With complete raw grids I now use the median spacing over all unique coordinates. The precise value moves slightly because the ASCII coordinates are decimal-quantized, but the physical conclusion is unchanged: the exported lattice is nominally 18 pixels, not 9.”

**Do not claim:** zero overlap, 32 px, 36 px, or 64 px has been proven.

## New slide 3 — M0/ASCII external execution is now exact-ID, not pathname-based

**On slide**

Canonical M0 chain:

`Drive file ID → provider size/MD5 → exact API download → SHA-256 → ffprobe → strict EOF decode → 4250–4500 audit`

Historical ASCII chain:

`Drive folder ID → exact 0001–0250 namespace → exact file-ID downloads → provider size/MD5 → 250 SHA-256 freeze`

- No whole-Drive recursive filename search.
- No manual frame inspection.
- No M1, selector freeze, or CFD unlock before canonical M0 PASS.

**Say:** “The remaining canonical video limitation is specific to the ChatGPT connector, not to the scientific workflow. The Colab route now downloads the exact Drive object by ID and independently binds the bytes before hashing and decoding. The same notebook separately freezes all 250 PIVlab exports.”

## Most defensible new scientific statement for tomorrow

> A stratified raw-byte audit of 13 complete historical PIVlab exports spanning the 250-field window found invariant pair mapping, calibration, 70×55 coordinate geometry and a fixed 1,192-cell active domain, while the direct-versus-interpolated vector composition changed across fields. The exported lattice is nominally 18 px, which remains inconsistent with a naive 18 px / 50%-overlap interpretation.

This statement is limited to what has actually been executed.
