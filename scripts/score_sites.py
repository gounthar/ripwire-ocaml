# Score sampled sites: enclosing fn (--uses), binding (--callees), candidate truth (--expand=Z::f).
import subprocess, sys, re, html, functools
B, ROOT, inp = sys.argv[1], sys.argv[2], sys.argv[3]
STDLIB = {'Map.Make', 'Set.Make', 'Hashtbl.Make', 'Weak.Make', 'Ephemeron.K1.Make', 'MoreLabels.Map.Make', 'Stdlib.Map.Make'}
@functools.lru_cache(None)
def run(arg):
    return subprocess.run([B, ROOT, '--no-cache', arg] + (['--limit=100000'] if arg.startswith('--uses') else ['--top-k=0'] if arg.startswith('--expand') else []),
                          capture_output=True, text=True).stdout
def attr(s, a):
    m = re.search(a + r'="([^"]*)"', s); return m.group(1) if m else ''
for line in open(inp):
    f, l, X, fn, kind, rhs = line.rstrip('\n').split('\t')
    u = run('--uses=' + fn)
    hdr = re.search(r'<uses [^>]*>', u); ndefs = attr(hdr.group(0), 'defs') if hdr else '?'
    sites = re.findall(r'<u role="call" p="([^"]*)" in_id="([^"]*)"', u)
    inid = next((html.unescape(i) for p, i in sites if p == f'{f}:{l}'), None)
    if not inid:
        print(f, l, f'{X}.{fn}', kind, rhs, ndefs, 'NO-SITE', '', '', '', sep='\t'); continue
    nsame = sum(1 for p, i in sites if html.unescape(i) == inid)
    c = run('--callees=' + inid)
    bound = sorted(set(re.findall(r'<s t="[a-z]*" n="' + re.escape(fn) + r'" p="([^"]*)"', c)))
    dec = attr(c, 'declined_calls') or '0'
    if kind == 'functor' and rhs in STDLIB:
        truth = ['OUTSIDE']
    else:
        e = run('--expand=' + rhs.split('.')[-1] + '::' + fn)
        truth = sorted(set(f'{p}:{ln}' for ln, p in re.findall(r'<b t="[^"]*" l="([0-9]*)" p="([^"]*\.ml)"', e)))
    if not bound:
        out = 'refused' if dec != '0' else 'unbound'
    elif truth == ['OUTSIDE']:
        out = 'wrong'
    elif not truth:
        out = 'CHECK-no-truth'
    elif set(bound) == set(truth):
        out = 'right'
    elif set(bound) & set(truth):
        out = 'CHECK-partial'
    else:
        out = 'wrong?'
    if nsame > 1 and out != 'refused':
        out += '+multi'
    print(f, l, f'{X}.{fn}', kind, rhs, ndefs, out, ' '.join(bound), ' '.join(truth), nsame, sep='\t')
