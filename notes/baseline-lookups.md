# Baseline lookups (step 2)

Corpus: xapi-project/xen-api `b132418b8934af5aae755aba8391c20db80b6bdf` (2026-10-02),
`/var/tmp/ripwire-ocaml/xen-api`. Locations below were found with `git grep` in that tree on
2026-10-14 [ran it]. They are the expected answers each tool is scored against.

Source of the lookups: the xcpng-riscv64 project notes (CONTEXT.md, local/log.md,
local/CONTEXT-2026-10-0{4,8}*.md, local/bootloader-130-options.md, docs/track-b-packages.md).
Each lookup was actually made during the RISC-V work. The notes recorded several of the
answers against `245b33a31` (the RISC-V xen-api build), not `b132418`, so their line numbers
differ by a few lines. I asked the xcpng-riscv64 session (IPC #1570) for more lookups. It replied at 17:00 with
ten; three overlap rows 1, 6, 8, the other seven are rows 12-18.

Kinds: **D** = find the definition, **C** = find the callers or readers.

| # | Lookup | Kind | Why it came up | Expected answer at b132418 |
|---|---|---|---|---|
| 1 | `Xapi_globs.xen_cmdline_script` / `xen_cmdline_path` | D+C | #135: does xapi pass more than one key per xen-cmdline call? | defs `xapi/xapi_globs.ml:874,947`; uses `xapi_host.ml:2914,2926`, `pciops.ml:72,113,136,140`, `xapi_host_max_cstate.ml:175,185` (inside `xen_cmdline_set`/`_get`, called at `xapi_host.ml:3484,3495`), `xapi_vm.ml:154` (in `set_dom0_memory`); config keys `xapi_globs.ml:2087,2265` |
| 2 | `Xapi_vm.set_dom0_memory` | D+C | #135 dom0_mem: can xapi write an unbootable value? | def `xapi/xapi_vm.ml:150`; callers same file `:180,:224` (unqualified) |
| 3 | `Hotplug.wait_for_unplug` | D+C | #90 forced shutdown hung on VIF unplug | def `xenopsd/xc/hotplug.ml:185`; caller `:281` (same file) |
| 4 | `Device.Generic.hard_shutdown` | D | #90 fix site [inferred from the round-11 note: "sets the blkback backend to Closing"] | `xenopsd/xc/device.ml:356`; decoys: other `hard_shutdown` at `:562`, `:965` (alias), `:1067` |
| 5 | `Xenopsd.run_hotplug_scripts` | D+C | does xenopsd run hotplug scripts itself (no uevent helper)? | ref `xenopsd/lib/xenopsd.ml:28`; read in `device.ml:346`; local wrapper `Generic.run_hotplug_scripts` `device.ml:345`, used `:351,:597,:743,:951,:979`; option table `xenopsd.ml:175-177`; also read and **written** (`:= false`) at `xenops_server_xen.ml:5596-5610` |
| 6 | `Service.PV_Vnc.start` | D+C | xenopsd starts vncterm for RISC-V guests | def in `xenopsd/xc/service.ml` (nested module, `debug` at `:956`); caller `xenops_server_xen.ml:2713` |
| 7 | xenstore key `vncterm-pid` | C | trap: replacing a guest's vncterm by hand | string literal, `xenopsd/xc/service.ml:870`. Not a symbol; grep-only for every tool |
| 8 | `set_domain_type` / `get_domain_type` (domain-type strings) | D | Anthony Perard: stop calling Arm/RISC-V guests "PVH" | `xenopsd/xc/xenops_server_xen.ml:1600,1614` (nested in a module of that file) |
| 9 | `Network_utils.Brctl.*` callers | C | does networkd's bridge backend need brctl? | `Brctl` module `networkd/lib/network_utils.ml:1946`; callers `networkd/bin/network_server.ml:1074,1076,1159,1160,1235,1242,1297,1320,1480,1482,1536` (11 sites) |
| 10 | `proxy` in wsproxy | D | #82 pv-vnc-N patch | `wsproxy/cli/wsproxy.ml:73`; decoys `xapi-stdext-unix/unixext.ml:397`, `xsh/xsh.ml:31` |
| 11 | `Xapi_vdi.update_allowed_operations` | C | appears 3x in the notes 9 non-test call sites: `message_forwarding.ml:1487,5358,5372,5849`, `xapi_ha.ml:1805,2087`, `xapi_vm.ml:46`, `xapi_xenops.ml:2637,2666` |

| 12 | `params_of_backend` | D | where backend-kind=vbd3 gets prepended | `xenopsd/xc/xenops_server_xen.ml:314` |
| 13 | `device_kind_of` (VBD) | D | where the VBD backend kind is chosen | `xenops_server_xen.ml:4127`; **same-file decoy**: the VIF `device_kind_of` at `:4975` |
| 14 | `extra_backend_keys` | D+C | VBD other-config:backend-kind into xenopsd | record field: `xapi-idl/xen/xenops_interface.ml:302`; set by xapi at `xapi/xapi_xenops.ml:727`; read in xenopsd `xenops_server_xen.ml:4129,4131` |
| 15 | `Xc_resources.vbd_script` | D+C | default /etc/xen/scripts/block and where hotplug runs it | `xenopsd/xc/xc_resources.ml:17`; use `hotplug.ml:307` |
| 16 | `Xapi_globs.sm_plugins` / `accept_sm_plugin` | D | SM plugin whitelist | `xapi/xapi_globs.ml:1414,1416` |
| 17 | `Sm_exec.xmlrpc_of_call` | D | the XML-RPC params struct built for an SM driver [name inferred from the riscv session's `sm_exec.ml:200-307`] | `xapi/sm_exec.ml:198` |
| 18 | `Xenctrl.domctl_create_config`, `hvm_param_get`, `hvm_check_pvdriver` | D | RISC-V domain create | **outside this corpus**: the bindings are in Xen's `tools/ocaml/libs/xc`. xen-api only re-exports the type (`xenopsd/xc/domain.ml:99`) and calls `hvm_param_get` (`domain.ml:799`); `hvm_check_pvdriver` has no hit |
| 19 | `Xc_resources.vncterm` | D | the vncterm binary path (follow-up to row 6) | `xenopsd/xc/xc_resources.ml:24` |
Nineteen lookups: #7 measures nothing a symbol index can do, so it stays as a
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
  These were gaps in my own narrow grep patterns, not OCaml resolution.
- **Second pass, after the riscv session listed `xapi_vm.ml:152` as a xen-cmdline caller:**
  the first pass had two holes of its own. The key-building grep was piped through
  `head -12` and silently truncated, and the unanchored pass excluded any file already in the
  key for *another* row. Re-run with no truncation and no exclusions [ran it]: rows 1, 5, 9
  and 11 were all short (row 11 missed 5 of 9 sites). All four are rewritten above from the
  complete lists. None of the missing sites needed OCaml resolution; every one is a plain
  textual match.

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
| 12 | `xenops_server_xen.ml:314` | **missed** (0 hits) |
| 13 | `xenops_server_xen.ml:4127` | **wrong one**: 1 hit, `:4975`, the VIF decoy |
| 14 | `xenops_interface.ml:302` | found (scope `Vbd/t`), plus `device.mli:100` |
| 15 | `xc_resources.ml:17` | found |
| 16 | `xapi_globs.ml:1414,1416` | found, both |
| 17 | `sm_exec.ml:198` | **missed** (0 hits) |
| 18 | outside corpus | n/a |
| 19 | `xc_resources.ml:24` | found, plus 1 decoy (`xenops_types.ml:127`, a record field) |

Score over the 17 rows with a definition in this corpus (7 is not a symbol, 18 is outside
the corpus):

| ctags result | rows | count |
|---|---|---|
| definition body found | 1, 3, 5, 9, 10, 14, 15, 16, 19 | 9 |
| only the `.mli` signature | 6, 11 | 2 |
| missed outright | 2, 4, 8, 12, 17 | 5 |
| returned the wrong same-name definition only | 13 | 1 |
| total | | 17 |

So 9 of 17 (53%). All hit lists checked
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

## git grep for definitions (the real bar)

A second side review: ctags is too easy a bar, since the `let NAME` grep used to build the key
found nearly every definition. Scored [ran it] with the exact fallback now in the
claude-config recipe (PR #305, `0eb6aff`):
`git grep -nE '^\s*(let|and) (rec )?SYM\b' -- 'ocaml/*.ml' 'ocaml/*.mli'`.

| row | found | hits | | row | found | hits |
|---|---|---|---|---|---|---|
| 1 | yes | 1 | | 11 | yes | 18 |
| 2 | yes | 1 | | 12 | yes | 1 |
| 3 | yes | 1 | | 13 | yes | 2 |
| 4 | yes | 17 | | 14 | no (record field) | 1 |
| 5 | yes | 2 | | 15 | yes | 1 |
| 6 | yes | 107 | | 16 | yes | 1 |
| 8 | yes | 4 | | 17 | yes | 1 |
| 9 | no (`module`, not `let`) | 0 | | 19 | yes | 1 |
| 10 | yes | 17 | | | | |

Recall 15 of 17, against ctags' 9. Both misses are the pattern's shape (`module Brctl`,
a `; extra_backend_keys:` field), and `module NAME` / `NAME:` variants would catch them.

So grep is the bar, and where it falls down is **noise, not recall**: rows 4, 6, 10 and 11
return 17, 107, 17 and 18 candidates for a name the user typed qualified
(`Device.Generic.hard_shutdown`, `PV_Vnc.start`, `Xapi_vdi.update_allowed_operations`).
Narrowing those to the one right definition, and the caller rows, is what OCaml support in
ripwire would have to add. The go/no-go note should score ripwire against grep on those
rows, not against ctags.
