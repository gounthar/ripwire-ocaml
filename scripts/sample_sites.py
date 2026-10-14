# Sample call sites `X.f` in .ml files where X is a module defined in the SAME file as a functor
# application (module X = F (..)) or an alias (module X = Y.Z). Prints file:line X f kind rhs.
# Skips matches inside a string or after `(*` on the same line; multi-line strings and comments still leak.
import os, re, random, sys
root = sys.argv[1]; n = int(sys.argv[2]); seed = int(sys.argv[3])
modre = re.compile(r'^\s*module ([A-Z][A-Za-z0-9_]*) = ([A-Z][A-Za-z0-9_.]*)\s*(\(.*)?$')
sites = []
for dp, _, fs in os.walk(os.path.join(root, 'ocaml')):
    for fn in fs:
        if not fn.endswith('.ml'): continue
        p = os.path.join(dp, fn)
        try: lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
        except OSError: continue
        mods = {}
        for i, l in enumerate(lines):
            m = modre.match(l)
            if m:
                kind = 'functor' if m.group(3) else 'alias'
                mods[m.group(1)] = (kind, m.group(2), i + 1)
        if not mods: continue
        callre = re.compile(r'(?<![A-Za-z0-9_.])(' + '|'.join(map(re.escape, mods)) + r')\.([a-z_][A-Za-z0-9_\']*)\s+[^=\s]')
        for i, l in enumerate(lines):
            if l.lstrip().startswith(('(*', 'module ', 'open ')): continue
            for m in callre.finditer(l):
                before = l[:m.start()]
                if before.count('"') % 2 == 1 or '(*' in before:
                    continue  # inside a string literal or a comment (single-line heuristic)
                k, rhs, defl = mods[m.group(1)]
                if i + 1 <= defl: continue
                sites.append((os.path.relpath(p, root), i + 1, m.group(1), m.group(2), k, rhs))
random.seed(seed)
print(f'# population {len(sites)} sites; functor {sum(s[4]=="functor" for s in sites)}, alias {sum(s[4]=="alias" for s in sites)}', file=sys.stderr)
for s in random.sample(sites, n):
    print(*s, sep='\t')
