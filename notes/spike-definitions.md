# Spike: OCaml definitions in ripwire (step 3)

Branch `spike/ocaml-defs` in `/var/tmp/ripwire-ocaml/ripwire-spike`, commit `09f609bc` on ripwire
`36753d62`. Local only. Corpus: xen-api `b132418` `ocaml/`, as in `baseline-lookups.md`.

## What the spike is

- tree-sitter-ocaml v0.26.0 (`e3c9cf36`), ABI 15, vendored in `third_party/deps/ocaml` (44 MB:
  `grammars/ocaml` 24 MB + `grammars/interface` 20 MB of generated C). The `type` sub-grammar is
  not vendored.
- One `Lang::OCaml` (tag `ml`); `.ml` uses the `ocaml` grammar and query set, `.mli` uses
  `tree_sitter_ocaml_interface` with the query set `ocaml_mli`. Same shape as `.ts`/`.tsx`.
- 14 source sites, found from the Clojure PR merge `a88f03d3` plus the compiler. `kParserVer` 901
  is a placeholder.
- Queries: definitions only. Structure-level `let` (anchored on `compilation_unit` / `structure`,
  so function-local `let ... in` is out), `external`, modules, module types, types, record fields,
  classes, methods; in `.mli`, `val`. Every `let` is `@definition.function`, because
  `parameter` is a child and not a field, and predicates do not run (#355).

Two things the Clojure template did not show [ran it]:

- `CMakeLists.txt` embeds each query in a raw string delimited by `CTXQ_<NAME>`. C++ limits the
  delimiter to 16 characters, so a query set called `ocaml_interface` fails to compile with
  "raw string delimiter longer than 16 characters" and "stray 'R'". The generator checks
  collisions, not length; a configure-time length check would be a one-line upstream fix.
- `kExtractFamilyByLang` in `src/ingest_sidecap.h` needs a row (static_assert). Put in
  `Scripting` with Elixir and Clojure.

## Build

Host: this WSL2 machine, x86_64, native, gcc 14.2.0, `-j6`, bash `time` [ran it].

| build | wall | user | sys |
|---|---|---|---|
| `main` `36753d62`, clean | 7m22.6s | 12m03.1s | 25.8s |
| spike, first attempt (failed at the two errors above) | 1m18.7s | 3m16.9s | 14.4s |
| spike, rebuild after the fixes (incremental over the failed attempt) | 6m24.1s | 9m10.7s | 14.6s |

The spike rebuild is not a clean build, so it is not a like-for-like comparison with `main`.

## Index

`ripwire xen-api/ocaml --no-cache`: 1.04 s wall, 11.2 s user [ran it]. 1709 files, 35738
symbols. `--skipped` census: `ml` 1413 files with symbols (a floor: symbol-less files are not
counted) of 1499 OCaml files, 33471 symbols. No OCaml file degraded-parse; 2 test files under
`libs/vhd/vhd_format_lwt_test/` flagged minified-suspect, still indexed.

## Definitions: 16 of 17

`--expand=NAME --top-k=0`, every returned body listed (none capped). Script:
`score_d.sh` in the session scratchpad; output `/var/tmp/ripwire-ocaml/spike-defs.txt`.

| row | found | defs returned | | row | found | defs returned |
|---|---|---|---|---|---|---|
| 1 | yes, both | 1 + 1 | | 11 | yes | 27 |
| 2 | yes | 1 | | 12 | yes | 1 |
| 3 | yes | 1 | | 13 | yes | 2 |
| 4 | yes | 21 | | 14 | **no** | 0 |
| 5 | yes | 2 | | 15 | yes | 1 |
| 6 | yes | 83 | | 16 | yes, both | 1 + 1 |
| 8 | yes, both | 5 + 3 | | 17 | yes | 1 |
| 9 | yes | 1 | | 19 | yes | 1 |
| 10 | yes | 5 | | | | |

| tool | definitions found |
|---|---|
| ctags 6.2.1 | 9 / 17 |
| `git grep '^\s*(let\|and) (rec )?SYM\b'` | 15 / 17 |
| spike | 16 / 17 |

- Row 14 (`extra_backend_keys`, a record field): the field is captured, `--grep` places
  `xenops_interface.ml:302` in symbol `t`, but `--expand` returns no body for a field
  [inferred: fields are not expandable symbols]. Not chased further.
- Row 9 (`module Brctl`) is the one grep's `let` pattern missed.
- **Noise is grep's noise.** Rows 4, 6, 11 return 21, 83 and 27 definitions, against grep's
  17, 107 and 18. The spike adds `.mli` `val`s, which grep's pattern also matched.

## Qualified selectors do not narrow

[ran it] `--expand=` with `Generic.hard_shutdown`, `Device.Generic.hard_shutdown`,
`PV_Vnc.start`, `Service.PV_Vnc.start`, `Xapi_vdi.update_allowed_operations`: **empty**, all
five. Only the `file.ml:name` form narrows, and to the file, not the module:
`device.ml:hard_shutdown` still returns every `hard_shutdown` in `device.ml` (356, 562, 965,
1067, 1706, ...), `service.ml:start` every `start` in `service.ml`.
`xapi_vdi.ml:update_allowed_operations` returns `.ml:539` and `.mli:47`, which is the right
answer, but only because the module is a file.

So with definitions alone the spike does not yet beat grep on rows 4, 6 and 11, the rows that
matter. That needs either the file-module scope (`xapi_vdi.ml` -> `Xapi_vdi`) plus nested-module
scopes, or the qualified-call resolver in `upstream-rules.md`. Whether `enclosingScopeOf` gives
OCaml `struct` scopes was not checked.

## Module scopes: qualified selectors now narrow

Spike commit on top of `09f609bc`: 53 added lines in four files [ran it, `git diff --stat`].

- `ocamlEnclosingScopeOf` (`ingest_names.h`): nearest `module_binding`, name read from its
  positional `module_name` child, skipping the binding's own name. Same shape as
  `kotlinEnclosingScopeOf`. Called from a new `Lang::OCaml` arm in the per-language scope
  dispatch in `ingest_sidecap.h`.
- `scopeOCamlFileModules` (`ingest_model.h`), called in `ingest.cpp` before `assignFields`: a
  top-level def with no enclosing module takes the capitalized file basename. It runs after
  capture because `captureTagsFacts` gets a `fileId`, not a path. dune `(wrapped true)`
  prefixes (`Lib__Xapi_vdi`) are not modelled; functors are scoped like plain modules.
- Rebuild, incremental, same host: 7m14.9s wall, 10m22.5s user, 18.1s sys [ran it].

`--expand=SEL --top-k=0 --no-cache` [ran it]:

| selector | before | after |
|---|---|---|
| `Generic::hard_shutdown` / `Generic.hard_shutdown` (row 4) | empty | `device.ml:356` only |
| `PV_Vnc::start` / `PV_Vnc.start` (row 6) | empty | `service.ml:955` + `service.mli:90` |
| `Xapi_vdi::update_allowed_operations` / `.` form (row 11) | empty | `xapi_vdi.ml:539` + `xapi_vdi.mli:47` |
| `Vif::hard_shutdown` (control: other module, same name) | not run | `device.ml:965` only |
| `Device::Generic` (file module on a module) | not run | `device.ml:111` + `device.mli:61` |
| `Nosuch::hard_shutdown` (negative control) | not run | matched no symbol |

All three rows land on the answer key, each with only the definition and its `.mli`
declaration (`service.mli:90` sits in `module PV_Vnc : sig` at line 78). Row 4 goes from 21
definitions to 1, row 6 from 83 to 2, row 11 from 27 to 2. The `.` spelling works without
any selector change [ran it; where ripwire splits on `.` was not traced].

**Cache trap.** Without `--no-cache` the same binary gave mixed answers (`PV_Vnc::start`
matched nothing, `Xapi_vdi.update_allowed_operations` matched). `kParserVer` is still the
placeholder 901, so the cache serves records from the scopeless build [inferred from the
`--no-cache` runs being consistent]. A PR bumps it.

**Callers: nothing to measure yet** at this commit. `--callers=Xapi_vdi::update_allowed_operations`
found both defs and returned `count="0"`, because the spike captured no references. Measured in
the next section.

**Data vs C++.** The maintainer asked for shared mechanisms over per-language C++. Scope is
per-language C++ today: Rust, Kotlin and Ruby each have a walker on `main` (`ingest_names.h`
924, 1009, 1045), so a fourth is precedented but runs against the stated preference. The OCaml
and Kotlin walkers are identical up to two strings (ancestor kind, name-child kind), so a shared
table-driven walker is a mechanism a PR could offer. The file-module scope has no node to read
and stays a special case.

## Callers: rows 6 and 11

Spike commit `8df054f6` on top of `56e64633`: 36 added lines in three files [ran it, `git diff --stat`].

- `queries/ocaml/tags.scm`: `(application_expression function: (value_path (value_name) @name))
  @reference.call`. Bare `f x` and qualified `M.f x`. Not captured: `x |> M.f`, `M.f` passed
  as a value, `M.(f x)` local opens, method calls `o#m`.
- `ocamlQualifierOf` (`ingest_names.h`) and an OCaml arm next to Rust's in `ingest_sidecap.h`:
  the immediate module of the `value_path` becomes the reference's qualifier
  (`Service.PV_Vnc.start` gives `PV_Vnc`). No `open`, alias or functor rewriting. The resolver
  is untouched: a qualified ref goes through the existing `qualifier::name` canonical tier,
  and falls to the bare-name ladder when that keys nothing.
- Rebuild, incremental, WSL2 x86_64 native, gcc 14.2, `-j6`, bash `time`: 8m6.3s wall,
  10m59.6s user, 20.1s sys [ran it].

Scored [ran it] with `--callers=SEL --no-cache` and `--uses=SEL --no-cache` against the answer
key in `baseline-lookups.md`. Each query takes 2.2 to 2.8 s wall, indexing included. The
resolver's edges are function to function, so a caller is scored as a function, then checked
against the key's sites. Four buckets: **correct**, **wrongly bound** (an edge to the target that
the source does not make), **refused** (a call captured but left unbound, `declined_calls=`),
**missed** (a key site the query never captured, which is the query's fault, not the resolver's).

| row | target | callers returned | correct | wrongly bound | refused | missed |
|---|---|---|---|---|---|---|
| 6 | `PV_Vnc::start` | 3 | 1 (`xenops_server_xen.ml:2713`) | **2** | 2 calls (`declined_calls=2`, not identified) | 0 |
| 11 | `Xapi_vdi::update_allowed_operations` | 19 (15 + 4 test) | 19, covering all 16 + 7 test key sites | 0 | 0 reported | 0 |

**Row 11 is clean.** The 9 qualified calls bind to the right definition [ran it], through the
canonical tier [inferred: `Xapi_vdi::update_allowed_operations` is keyed, and the decoys below bind
to their own keys]. The 7 unqualified calls inside `xapi_vdi.ml` also bind correctly; how the ladder
picked the right one of 27 same-named definitions was not traced. The decoy at `xapi_vdi.ml:1108`, `Xapi_sr_operations.update_allowed_operations`,
binds to its own target: `clone` is listed as a caller of `Xapi_sr_operations::update_allowed_operations`
[ran it].

**Row 6's two wrong edges** are `Varstored.start` (`service.ml:685`) and `Swtpm.start` (`:778`).
They call `Xenops_sandbox.Varstore_guard.start` and `Swtpm_guard.start`. Both modules are functor
applications (`xenops_sandbox.ml:237-238`, `module Varstore_guard = Guard (Varstored)`), so no
definition is keyed `Varstore_guard::start`; the real one is `Guard`'s, at `xenops_sandbox.ml:158`.
The canonical tier keys nothing, the ref falls to the bare-name ladder, and the ladder picks
`PV_Vnc.start`. This is the gap `upstream-rules.md` predicted (slice 6a) and the first measured
instance of it.

How often that path is taken: `xen-api` `ocaml/*.ml` holds 765 functor-application modules
(`module X = F (Y)`) and 520 plain aliases (`module X = Y.Z`) [ran it, `git grep -E` on the line
shape, so a lower bound: multi-line forms are not counted]. A call qualified by any of them
ladders the same way. How many such calls bind wrongly, as opposed to being declined, was not
measured.

**`--uses` prints sites from the same function, not the same binding.** `--uses=Xapi_vdi::update_allowed_operations`
returns 31 sites: the 23 in the key plus 8 calls to other modules' `update_allowed_operations`
(`Xapi_vbd_helpers`, `Xapi_vif_helpers`, `Xapi_vusb_helpers`, `Xapi_vm_lifecycle`,
`Xapi_sr_operations`). Each of the 8 sits in a function that also makes a true call. That is how
`--uses` narrows: it keeps a call site when its enclosing function has an edge to the target
(`verbs_navigate.h:557-583`, used at `:638`), and its comment says so. Not OCaml-specific. It
matters here because xapi functions call several same-named `update_allowed_operations` in a row,
so `p=` lines from `--uses` need reading before being trusted.

Against grep on the same rows (`baseline-lookups.md`): row 6, bare grep returns 782 hits, and
qualified grep finds the one caller with no noise. ripwire returns 3 callers, 1 of them right.
Row 11, qualified grep finds 16 of 23 and misses every same-file call; bare grep finds all 25
in 179 hits. ripwire returns 19 callers, all right.

## Parser robustness issue

The spike hit a robustness issue in the vendored grammar that can stop an index run. Real xen-api
code does not trigger it. Details are held until it is reported to tree-sitter-ocaml. A PR would
need a pre-parse guard for it, with a gate; ripwire already has guards of that kind for other
languages.

## For the decision note

- Parse rate and definitions are not the risk: 100% parse, 16/17, and a 1 s index.
- PR cost beyond the spike: the pre-parse guard and its gate, fixtures and a red-first
  gate, the 30-argv byte-identity diff, ASan, docs and counts.
- Definitions with module scopes beat grep on rows 4, 6 and 11 (1-2 defs against 17, 107, 18).
  Caller rows 6 and 11 are unmeasured: the spike has no references.
- Acceptance risk: scope needs per-language C++ (a fourth walker), against the maintainer's
  stated preference; offer a table-driven shared walker.
