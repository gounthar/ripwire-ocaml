# ripwire contribution rules that bear on the decision

Read [read file] at ripwire `36753d62` (`/var/tmp/ripwire-ocaml/ripwire`), 2026-10-14.

## Formalities

- No DCO, no CLA, no `Signed-off-by`. The only condition is the last paragraph of
  `CONTRIBUTING.md` §7: contributions are licensed under `LICENSE` (Apache-2.0) and follow
  `CODE_OF_CONDUCT.md`.
- No `.github/pull_request_template.md`, no issue templates.
- `AGENTS.md` and `CLAUDE.md` are build and test instructions (no build type, gate first,
  determinism, sanitizer build before a PR). Nothing in them is addressed to agents beyond that,
  and no AI-disclosure policy either way.
- Before review: full gate suite (`python3 test/pargates.py . ./build/ripwire -j 6`), ASan build,
  determinism gate three times, 30+ argv byte-identity diff against a `main` binary, `kParserVer`
  bump (and its mirror in `src/quality.h`) when extraction output moves.
- Build memory: `src/main.cpp` needs about 3 GB per parallel job under gcc, 2 GB under clang
  (`CONTRIBUTING.md` §1 "Building on Linux"). Too little memory does not fail with a diagnostic.

## What matters for OCaml call edges (CONTRIBUTING.md §3, "Adding a language")

The caller scoring in `baseline-lookups.md` says the only rows where an index can beat grep are
6 and 11: binding a bare or module-qualified name to its module. That is the part upstream does
not have yet:

- "No language-neutral qualified-call resolver exists yet (`src/elixir_resolve.h` is
  Elixir-specific); generalising it is slice 6b." Slice 6b is sized M, open to claim, with
  Clojure named as the first new user.
- Known gap: a language that newly sets `Reference::qualifier` gets no refusal. When no
  `qualifier::name` definition is found, the call falls through to the bare-name ladder, so
  Clojure's `str/join` binds an in-tree `join`. The shared refusal is slice 6a, marked
  *maintainers*, "not yet scheduled".
- A wrong edge the PR does not fix must be pinned as a known-gap arm, and a per-language guard
  for one language alone is explicitly refused.

Consequence [inferred]: an OCaml PR can deliver definitions on its own. Call edges are less
clear-cut than "everything ladders". The bare-name ladder applies only when the canonical tier
finds no `qualifier::name` definition. If OCaml top-level definitions get scoped to their file's
module (`xapi_vdi.ml` -> `Xapi_vdi`), the 16 qualified calls on row 11 could bind correctly
through the existing canonical tier. What would ladder is the rest: the 7 same-file calls with no
qualifier, calls through `open` (row 9), and qualifiers naming a nested or external module.
Whether ripwire gives a file a module scope at all is untested; the spike has to measure it.
In the worst case, `update_allowed_operations` binds to every same-named definition in the tree
(the 179-hit row), pinned as a known gap. That is grep's
noise again, inside a tool that presents it as a call graph. Doing 6b ourselves is the
alternative, and it is the maintainers' design to agree first.

Also relevant: tags-pass predicates (`#eq?`, `#any-of?`) do not run yet (#355, slice 5a), so a
`tags.scm` cannot filter by node text.
