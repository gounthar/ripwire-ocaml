# Decision note: OCaml support for ripwire (#377)

2026-10-14. Corpus xen-api `b132418`, ripwire `36753d62`, spike `56e64633` (local only).
Detail lives in `baseline-lookups.md`, `spike-definitions.md` and `upstream-rules.md`.

## Recommendation

**Conditional go.** The definitions half is measured and worth it. The callers half, which is
the half grep is worst at, is not measured yet. One more spike step (reference captures on
rows 6 and 11) decides it, before anything is said on #377.

Nothing has been posted upstream. Whether and when to comment on #377 is Bruno's call.

## What is measured

| question | grep | ctags | spike | evidence |
|---|---|---|---|---|
| definitions found (17 rows) | 15 | 9 | 16 | ran it |
| row 4 `Generic.hard_shutdown`, defs returned | 17 | | 1 | ran it |
| row 6 `PV_Vnc.start`, defs returned | 107 | | 2 (`.ml` + `.mli`) | ran it |
| row 11 `Xapi_vdi.update_allowed_operations`, defs returned | 18 | | 2 (`.ml` + `.mli`) | ran it |
| callers, row 6 / row 11 | 782 / 179 hits, every site found | | **not measured** | ran it (grep only) |
| parse rate, xen-api `.ml` / `.mli` | | | 1052/1052, 451/451 | #377 STEP 0 |
| index time, xen-api `ocaml/` | | | 1.04 s wall | ran it |

What changes for the RISC-V xen-api work: "where is `Module.f` defined" goes from a page of grep
hits to the one definition and its signature. Bruno confirmed the xen-api work runs for months
past Oct 30, so the need is there.

## What is not measured, and why it decides the callers half

- The spike captures no references. `--callers=Xapi_vdi::update_allowed_operations` returns
  `count="0"` for that reason alone.
- Definitions now carry module scopes, so a call written `Xapi_vdi.update_allowed_operations`
  should key the existing canonical `qualifier::name` tier [inferred from `upstream-rules.md`,
  untested]. Row 11 has 16 such calls.
- What would not bind that way: 7 same-file unqualified calls, calls through `open`, and
  qualifiers naming nested or external modules. Without the shared refusal (slice 6a,
  maintainers, unscheduled) those fall to the bare-name ladder and bind every same-named
  definition: grep's noise presented as a call graph.
- Next measurement: call captures in `tags.scm` with the qualifier set on the reference, then
  precision on rows 6 and 11 against the hand-checked answer key, counting refused against
  wrongly bound edges.

## What a PR would cover

Would cover:

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
- Call edges, unless the next measurement shows the canonical tier binds them cleanly.

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
(53 lines). Left for a definitions PR: the pre-parse guard and its gate, the shared walker refactor,
fixtures and gates, the pre-review checklist. Builds take 6 to 7 minutes on this machine, so
each gate iteration costs that. No day estimate: nothing here measured one.

## Decision path

1. Spike reference captures; measure rows 6 and 11 callers (precision, refusals).
2. If callers bind cleanly through the canonical tier: go for a definitions-plus-calls PR.
   If they ladder into noise: go for a definitions-only PR, call edges named as the gap
   waiting on 6a/6b.
3. Either way, comment on #377 first asking for the starting files (the maintainer offered),
   and propose the table-driven scope walker before writing it. Draft → `/pr-voice` → Bruno.
4. Separately, report the grammar robustness issue to tree-sitter-ocaml.
