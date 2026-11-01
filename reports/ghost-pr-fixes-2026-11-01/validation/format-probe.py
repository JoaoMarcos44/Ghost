"""Explain the broad formatting failure using unchanged main files only."""
from pathlib import Path
import difflib, json, os, runpy, subprocess, tempfile, tarfile, io

root = Path(r'C:\Users\Nitro\Ghost')
source = root / '.worktrees/fix-settings-pending-save-20261031'
helper = runpy.run_path(str(root / 'reports/ghost-prs-2026-10-31/validation/run_checks.py'), run_name='helpers')
scratch = Path(tempfile.mkdtemp(prefix='.tmp-sandbox-validation-format-', dir=root))
node = source / 'node_modules/.bin/node.exe'
paths = ['tools/scripts/lib/pnpm.ts', 'packages/testing/test-data/src/selectors/billing.ts']
result = {}
try:
    for path in ['.editorconfig', '.oxfmtrc.json', 'package.json', 'pnpm-workspace.yaml', 'pnpm-lock.yaml', *paths]:
        dest = scratch / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(subprocess.check_output(['git', 'show', '3b395b6b082bb995bc8dc8d7b648fea7732fe839:' + path], cwd=root))
    before = {path: (scratch/path).read_bytes() for path in paths}
    for label, options in [('default_archive', []), ('lf_archive', ['-c', 'core.autocrlf=false'])]:
        archive = subprocess.check_output(['git', *options, 'archive', '3b395b6b082bb995bc8dc8d7b648fea7732fe839', *paths], cwd=root)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            result[label] = {path: {'crlf': (data := tar.extractfile(path).read()).count(b'\r\n'), 'matches_blob': data == before[path]} for path in paths}
    env = os.environ.copy()
    env.update(TEMP=str(scratch), TMP=str(scratch), XDG_CACHE_HOME=str(scratch/'cache'), NODE_OPTIONS='--max-old-space-size=2048')
    env.update(pnpm_config_verify_deps_before_run='false', pnpm_config_offline='true', PATH=str(node.parent)+os.pathsep+env['PATH'])
    pnpm = Path(r'C:\Users\Nitro\AppData\Local\pnpm\.tools\pnpm\12.16.1_tmp_22488_0\node_modules\@pnpm\exe.win32-x64\pnpm.exe')
    helper['dependency_links'](source, scratch, ['package.json'], node)
    probe = subprocess.run([str(pnpm), 'exec', 'oxfmt', '--check', '--threads=1', *paths], cwd=scratch, env=env, capture_output=True, text=True, timeout=60)
    result['pnpm_probe'] = {'exit': probe.returncode, 'output': probe.stdout + probe.stderr}
    subprocess.run([str(node), str(source/'node_modules/oxfmt/bin/oxfmt'), '--threads=1', *paths], cwd=scratch, env=env, check=True, timeout=60)
    for path in paths:
        after = (scratch/path).read_bytes()
        result[path] = {'changed': before[path] != after, 'before_crlf': before[path].count(b'\r\n'), 'after_crlf': after.count(b'\r\n'),
                        'diff': ''.join(difflib.unified_diff(before[path].decode().splitlines(True), after.decode().splitlines(True), n=2))}
    print(json.dumps(result), flush=True)
    (root/'reports/ghost-pr-fixes-2026-11-01/validation/format-probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
finally:
    helper['remove_sandbox'](scratch)
