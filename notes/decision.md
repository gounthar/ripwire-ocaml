# Decision note: OCaml support for ripwire (#377)

2026-10-14. Corpus xen-api `b132418`, ripwire `36753d62`, spike `8df054f6` (local only).
Detail lives in `baseline-lookups.md`, `spike-definitions.md` and `upstream-rules.md`.

## Recommendation

**Go for definitions. Call edges: a provisional go, on a small sample.** Definitions are
measured on 17 rows and worth it outright. Call edges rest on two hand-checked lookups plus a
20-site sample of the risky path:

- Row 11, qualifier naming a file module: 19 of 19 callers right (grep: 179 hits).
- Row 6, qualifier naming a functor-built module: 2 of 3 callers wrong.
- 20 random calls through functor-built or aliased modules (of 3,478): 12 right, 7 refused,
  1 wrong. Both wrong cases so far are functor-built modules, binding as a split across unrelated
  same-named definitions. The wrong rate is somewhere between 1% and 24% (95% interval), which
  bounds the problem but does not size it.

The condition for call edges stays: a qualified OCaml call whose qualifier keys nothing should
be refused, not laddered. That is slice 6a, the maintainers' shared refusal, so it is the question
to put on #377. A bigger sample, or a corpus-wide count, should come before claiming a rate.

Nothing has been posted upstream. Whether and when to comment on #377 is Bruno's call.

## What is measured

| question | grep | ctags | spike | evidence |
|---|---|---|---|---|
| definitions found (17 rows) | 15 | 9 | 16 | ran it |
| row 4 `Generic.hard_shutdown`, defs returned | 17 | | 1 | ran it |
| row 6 `PV_Vnc.start`, defs returned | 107 | | 2 (`.ml` + `.mli`) | ran it |
| row 11 `Xapi_vdi.update_allowed_operations`, defs returned | 18 | | 2 (`.ml` + `.mli`) | ran it |
| callers, row 6 / row 11 | 782 / 179 hits, every site found | | 3 callers, 1 right / 19 callers, 19 right | ran it |
| parse rate, xen-api `.ml` / `.mli` | | | 1052/1052, 451/451 | #377 STEP 0 |
| index time, xen-api `ocaml/` | | | 1.04 s wall | ran it |

What changes for the RISC-V xen-api work: "where is `Module.f` defined" goes from a page of grep
hits to the one definition and its signature. Bruno confirmed the xen-api work runs for months
past Oct 30, so the need is there.

## What the callers measurement showed

Detail in `spike-definitions.md`, Callers: rows 6 and 11.

- Applications are captured as calls, with the immediate module of the path as the qualifier.
  36 lines, no resolver change.
- Qualifier names a file module or a `struct` module: the canonical `qualifier::name` tier binds
  it [ran it on row 11; mechanism inferred]. Same-file unqualified calls also came out right on
  row 11 (mechanism not traced).
- Qualifier names a functor application (`module Varstore_guard = Guard (Varstored)`): nothing is
  keyed under it, the ref falls to the bare-name ladder, and on row 6 the ladder bound
  `Varstore_guard.start` and `Swtpm_guard.start` to `PV_Vnc.start`. 765 functor applications and
  520 aliases in `ocaml/*.ml` take the same path [ran it, line-shape grep, lower bound]. How many
  of their calls bind wrongly rather than being declined: sampled, 1 of 20 wrong (see
  `spike-definitions.md`, Sample).
- Not captured at all: `|>` pipelines, functions passed as values, `M.( )` local opens. These
  are misses in the query, not wrong bindings; neither row hit one.
- `--uses` lists every same-named call in a function that has a true edge, so its `p=` lines
  over-report on xapi code (8 extra sites on row 11). Language-neutral, not an OCaml issue.

## What a PR would cover

Would cover:

- Call edges for applications, qualifier set from the module path, only once the shared
  refusal (slice 6a) is in place for qualifiers that key nothing.
- Vendored tree-sitter-ocaml v0.26.0 pinned by SHA, one `Lang::OCaml`, `.ml` and `.mli` query
  sets (the spike shape).
- Definitions with module scopes: nested `module X = struct` and the file module.
- A pre-parse guard for the grammar robustness issue (`spike-definitions.md`, Parser
  robustness). Required, not optional.
- Fixtures, red-first gates, ASan, determinism, the 30-argv byte-identity diff, a real
  `kParserVer` bump.

Would not cover (stated as known gaps):

- dune `(wrapped true)` library prefixes, functor application, first-class modules, ppx-generated
  definitions (`[@@deriving rpc]`).
- Record-field lookups (row 14), which need types.
- Call edges through functor applications, aliases, `open`, pipelines and functions passed as
  values. The first two need the refusal above to be safe; the rest are simply not captured.

## Acceptance risk

The maintainer asked for data (pinned grammar plus capture queries) and shared mechanisms over
per-language C++. Two parts of this cannot be pure data today:

1. **Scope.** Assigned by a per-language C++ walker (`ingest_sidecap.h` dispatch). Rust, Kotlin
   and Ruby each have one on `main`, so a fourth is precedented, but it runs against the stated
   preference. The OCaml walker and `kotlinEnclosingScopeOf` differ only in two node-kind strings,
   so a PR can offer one table-driven walker for both instead. The file-module scope has no
   node to read and stays a small special case.
2. **The pre-parse guard** for the robustness issue, which has precedent in other languages.

Also: 44 MB of generated grammar C in `third_party/`, against Clojure's precedent (merged, #349)
and Gleam's (closed, #64). Why Gleam closed was not checked.

## Effort, in pieces rather than days

Done in the spike: grammar vendoring, Lang wiring at 14 sites, definition queries, scopes
(53 lines), call captures (36 lines). Left for a definitions PR: the pre-parse guard and its
gate, the shared walker refactor, fixtures and gates, the pre-review checklist. Builds take 6 to 8 minutes on this machine, so
each gate iteration costs that. No day estimate: nothing here measured one.

## Decision path

1. Done: rows 6 and 11 measured. Neither clean nor noise: right where the qualifier keys a
   scope, wrong where it names a functor application.
2. Ask on #377 whether the shared refusal (slice 6a) can land with OCaml call-edge support.
   An OCaml-only guard is not an option: upstream refuses per-language guards
   (`upstream-rules.md`). If 6a cannot come first, call edges wait for it, and a
   definitions-only PR goes alone.
3. Either way, comment on #377 first asking for the starting files (the maintainer offered),
   and propose the table-driven scope walker before writing it. Draft → `/pr-voice` → Bruno.
4. Separately, report the grammar robustness issue to tree-sitter-ocaml.
