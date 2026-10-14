# Baseline lookups (step 2)

Corpus: xapi-project/xen-api `b132418b8934af5aae755aba8391c20db80b6bdf` (2026-10-02),
`/var/tmp/ripwire-ocaml/xen-api`. Locations below were found with `git grep` in that tree on
2026-10-14 [ran it]. They are the expected answers each tool is scored against.

Source of the lookups: the xcpng-riscv64 project notes (CONTEXT.md, local/log.md,
local/CONTEXT-2026-10-0{4,8}*.md, local/bootloader-130-options.md, docs/track-b-packages.md).
Each lookup was actually made during the RISC-V work. The notes recorded several of the
answers against `245b33a31` (the RISC-V xen-api build), not `b132418`, so their line numbers
differ by a few lines. I asked the xcpng-riscv64 session (IPC #1570) for more lookups; no
reply yet.

Kinds: **D** = find the definition, **C** = find the callers or readers.

| # | Lookup | Kind | Why it came up | Expected answer at b132418 |
|---|---|---|---|---|
| 1 | `Xapi_globs.xen_cmdline_script` / `xen_cmdline_path` | D+C | #135: does xapi pass more than one key per xen-cmdline call? | defs `xapi/xapi_globs.ml:874,947`; uses `xapi_host.ml:2914,2926`, `pciops.ml:72,113,136,140`, `xapi_host_max_cstate.ml:175,185` (inside `xen_cmdline_set`/`_get`, called at `xapi_host.ml:3484,3495`) |
| 2 | `Xapi_vm.set_dom0_memory` | D+C | #135 dom0_mem: can xapi write an unbootable value? | def `xapi/xapi_vm.ml:150`; callers same file `:180,:224` (unqualified) |
| 3 | `Hotplug.wait_for_unplug` | D+C | #90 forced shutdown hung on VIF unplug | def `xenopsd/xc/hotplug.ml:185`; caller `:281` (same file) |
| 4 | `Device.Generic.hard_shutdown` | D | #90 fix site [inferred from the round-11 note: "sets the blkback backend to Closing"] | `xenopsd/xc/device.ml:356`; decoys: other `hard_shutdown` at `:562`, `:965` (alias), `:1067` |
| 5 | `Xenopsd.run_hotplug_scripts` | D+C | does xenopsd run hotplug scripts itself (no uevent helper)? | ref `xenopsd/lib/xenopsd.ml:28`; read in `device.ml:346`; local wrapper `Generic.run_hotplug_scripts` `device.ml:345`, used `:351,:597`; also read and **written** (`:= false`) at `xenops_server_xen.ml:5596-5610` |
| 6 | `Service.PV_Vnc.start` | D+C | xenopsd starts vncterm for RISC-V guests | def in `xenopsd/xc/service.ml` (nested module, `debug` at `:956`); caller `xenops_server_xen.ml:2713` |
| 7 | xenstore key `vncterm-pid` | C | trap: replacing a guest's vncterm by hand | string literal, `xenopsd/xc/service.ml:870`. Not a symbol; grep-only for every tool |
| 8 | `set_domain_type` / `get_domain_type` (domain-type strings) | D | Anthony Perard: stop calling Arm/RISC-V guests "PVH" | `xenopsd/xc/xenops_server_xen.ml:1600,1614` (nested in a module of that file) |
| 9 | `Network_utils.Brctl.*` callers | C | does networkd's bridge backend need brctl? | `Brctl` module `networkd/lib/network_utils.ml:1946`; callers `networkd/bin/network_server.ml:1074..1482` (10 sites) |
| 10 | `proxy` in wsproxy | D | #82 pv-vnc-N patch | `wsproxy/cli/wsproxy.ml:73`; decoys `xapi-stdext-unix/unixext.ml:397`, `xsh/xsh.ml:31` |
| 11 | `Xapi_vdi.update_allowed_operations` | C | appears 3x in the notes | 4 call sites in `xapi/message_forwarding.ml` (`:1487,5358,5372,5849`), plus tests |

Eleven lookups, not ten: #7 measures nothing a symbol index can do, so it stays as a
control. What each tool should *say* there is "not a symbol".

## What the baseline measures, per lookup

- D: does `ctags` return the expected file:line among its hits, and how many decoys come
  with it (rows 4 and 10 are the name-collision cases).
- C: ctags has no answer for callers. The honest baseline for C is `git grep -n` on the name,
  scored as recall (expected sites found) and noise (hits that are not uses: comments,
  strings, same-name other symbols).

## Answer-key audit (2026-10-14)

A side review pointed out that the key above was built with `git grep`, which is the very
tool scored for the C rows, so grep would score perfectly by construction. Checked [ran it]:

- **Open/alias/include scan.** For every C target, listed the files that `open`, `include` or
  alias its module (`module X = M`, `let open M`, `M.( )`), then grepped them for the bare
  name, plus every alias `X.name`. Nothing new, except the `Brctl.*` sites in
  `network_server.ml`, which bind through `open Network_utils` and were already in the key.
- **Dune wrapped-library paths** (`Lib.Hotplug.wait_for_unplug` etc.): none.
- **Unanchored grep on the bare names**, outside the files already in the key: found
  `xapi_host_max_cstate.ml:175,185` (row 1) and `xenops_server_xen.ml:5596-5610` (row 5).
  These were gaps in my own narrow grep patterns, not OCaml resolution. Rows 1 and 5 are
  corrected above.

Remaining limit: this is still a lexical check. A reference through a functor argument, a
first-class module, or a function passed as a value under another name would not show up.
Only a type-aware index (merlin / `ocaml-index`, which needs the opam build parked in
CLAUDE.md) closes that. **The C-row scores are therefore an upper bound for grep.**

## ctags results (definitions)

Host: a Fedora x86_64 machine, Universal Ctags 6.2.1, on `git archive b132418 ocaml`
(`/var/tmp/ripwire-ocaml/xen-api-b132418`, 1049 `.ml` / 450 `.mli`; the other 3+1 files are
outside `ocaml/`). Index: `ctags -R --fields=+nKZ --languages=OCaml ocaml`, 31264 tags,
wall 0.22 s, user 0.17 s [ran it].

| # | Expected definition | ctags |
|---|---|---|
| 1 | `xapi_globs.ml:874,947` | found, both, 1 hit each |
| 2 | `xapi_vm.ml:150` | **missed** (0 hits for the name) |
| 3 | `hotplug.ml:185` | found, 1 hit |
| 4 | `device.ml:356` (`Generic.hard_shutdown`) | **missed**; 9 hits, none at 356 or 562 (has `device.ml:1067,1706`, `.mli`s, others) |
| 5 | `xenopsd.ml:28` | found, 1 hit |
| 6 | `service.ml:955` `PV_Vnc.start` | **missed in `.ml`**; `start` has 55 hits, the only `service.ml` one is `:591` (Vgpu). The signature is there: `service.mli:90`, scope `PV_Vnc` |
| 8 | `xenops_server_xen.ml:1600,1614` | **missed**; `set_domain_type` hits are xapi's (`message_forwarding.ml`, `xapi_vm.mli`), `get_domain_type` only squeezed's |
| 9 | `network_utils.ml:1946` (`Brctl`) | found |
| 10 | `wsproxy.ml:73` | found, plus 2 decoys (`unixext.ml/.mli`) |
| 11 | `xapi_vdi.ml` def | **missed** in `.ml`; `xapi_vdi.mli:47` present among 17 hits |

Score: 5 of 10 definition lookups found the body; 2 more (rows 6, 11) only reach the `.mli`
signature; 3 missed outright (rows 2, 4, 8). Row 7 is not a symbol. All hit lists checked
in full, not truncated.

### Why: ctags' OCaml parser drops definitions

Corpus-wide check [ran it]: of 14457 column-0 `let`/`let rec` definitions in `.ml` files,
ctags tags 9107 at the same line, **63.0%**. Per file: 489 of 966 files at 100%, 264 above
50%, 209 below 50%, 4 at 0% (e.g. `xapi/repository.ml`, `xapi/xapi_observer.ml`).
`xapi_vm.ml` has 128 top-level lets and 15 tags. The column-0 regex is my own ground truth:
it skips `let%ppx`, `let () =`, and nested-module definitions, so it measures top-level
recall only.

Not yet known: which construct makes the parser lose sync. The `b40405f` recipe in
`~/.claude/CLAUDE.md` says "definitions only", which reads as complete for definitions. It is
not, and the recipe should say so.
