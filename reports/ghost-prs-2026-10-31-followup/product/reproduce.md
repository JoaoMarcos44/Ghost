# Product card HTML import — isolated test runner

Run from PowerShell with `PRODUCT_PHASE=red` before the parser fix, `PRODUCT_PHASE=green` after it, or `PRODUCT_PHASE=lint` for targeted ESLint checks. The runner copies Koenig sources to a temporary sandbox, resolves workspace source exports there, limits Vitest to one worker and removes the sandbox when finished. The RED phase accepts only the expected assertion failures in both files.

```powershell
$env:PRODUCT_PHASE = 'green'
$env:PYTHONIOENCODING = 'utf-8'
$report = Get-Content -LiteralPath 'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31-followup\product\reproduce.md' -Raw -Encoding UTF8
$match = [regex]::Match($report, '(?s)<!-- BEGIN RUNNER -->\s*```python\s*\n(.*?)\n```\s*<!-- END RUNNER -->')
if (-not $match.Success) { throw 'Runner not found' }
$match.Groups[1].Value | python -
exit $LASTEXITCODE
```

<!-- BEGIN RUNNER -->
```python
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
repo = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-product-card-button-import-20261031').resolve(strict=True)
node = r'C:\Users\Nitro\ghost-functional-audit\source\node_modules\.bin\node.exe'
pnpm = r'C:\Users\Nitro\AppData\Roaming\npm\node_modules\pnpm\bin\pnpm.cjs'
phase = os.environ.get('PRODUCT_PHASE', 'red')
if phase not in ('red', 'green', 'lint'):
    raise SystemExit('PRODUCT_PHASE must be red, green or lint')
for name in ('node_modules', 'koenig/kg-default-nodes/node_modules', 'koenig/kg-html-to-lexical/node_modules'):
    if not (repo / name).is_dir():
        raise SystemExit(f'Bootstrap dependency missing: {repo / name}')
env = os.environ.copy()
env.update(NODE_OPTIONS='--max-old-space-size=4096 --conditions=source', UV_THREADPOOL_SIZE='1', NX_DAEMON='false', CI='true', pnpm_config_verify_deps_before_run='false')
env['PATH'] = str(Path(node).parent) + os.pathsep + r'C:\Program Files\Git\bin' + os.pathsep + env['PATH']
target = None
results = []

def junction(link, destination):
    linkenv = env.copy()
    linkenv['TASK_JUNCTION_LINK'] = str(link)
    linkenv['TASK_JUNCTION_TARGET'] = str(destination)
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                    'New-Item -ItemType Junction -Path $env:TASK_JUNCTION_LINK -Target $env:TASK_JUNCTION_TARGET -ErrorAction Stop | Out-Null'],
                   env=linkenv, check=True)

try:
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-product-', dir=str(repo)) as temporary:
        target = Path(temporary).resolve(strict=True)
        if target.parent != repo or not target.name.startswith('.tmp-sandbox-product-') or target.is_symlink():
            raise RuntimeError('Unexpected sandbox path')
        print(f'SANDBOX={target}', flush=True)
        env['TEMP'] = env['TMP'] = str(target)
        env['XDG_CACHE_HOME'] = str(target / '.cache')
        env['NPM_CONFIG_USERCONFIG'] = str(target / 'npm-user-empty')
        env['NPM_CONFIG_GLOBALCONFIG'] = str(target / 'npm-global-empty')
        koenig = target / 'koenig'
        koenig.mkdir()
        shutil.copy2(repo / 'koenig/vitest.shared.ts', koenig / 'vitest.shared.ts')
        links = []
        try:
            junction(target / 'node_modules', repo / 'node_modules')
            links.append(target / 'node_modules')
            packages = ('kg-default-nodes', 'kg-html-to-lexical', 'kg-default-transforms', 'kg-clean-basic-html', 'kg-markdown-html-renderer', 'kg-utils')
            aliases = []
            for name in packages:
                source = repo / 'koenig' / name
                dest = koenig / name
                shutil.copytree(source, dest, ignore=shutil.ignore_patterns('node_modules', 'build', 'coverage', '.vite', '*.tsbuildinfo'))
                junction(dest / 'node_modules', source / 'node_modules')
                links.append(dest / 'node_modules')
                package = json.loads((dest / 'package.json').read_text(encoding='utf-8'))
                for subpath, condition in package.get('exports', {}).items():
                    if isinstance(condition, dict) and 'source' in condition:
                        module_name = package['name'] + ('' if subpath == '.' else subpath[1:])
                        aliases.append({'find': module_name, 'replacement': (dest / condition['source']).as_posix()})
            aliases.sort(key=lambda entry: len(entry['find']), reverse=True)
            for name in ('kg-default-nodes', 'kg-html-to-lexical'):
                dest = koenig / name
                cache = (target / '.vite' / name).as_posix()
                config = "import {mergeConfig} from 'vitest/config';\nimport base from './vitest.config';\nexport default mergeConfig(base, {cacheDir: " + json.dumps(cache) + ", resolve: {alias: " + json.dumps(aliases) + ", conditions: ['source', 'node']}, test: {server: {deps: {inline: [/^@tryghost\\/kg-/]}}}});\n"
                (dest / 'vitest.sandbox.config.ts').write_text(config, encoding='utf-8')
            commands = [
                ('kg-default-nodes', 'test/nodes/product.test.ts', 'product button after a linked description|product button disabled when only description is linked',
                 ['imports a product button after a linked description', 'keeps a product button disabled when only description is linked']),
                ('kg-html-to-lexical', 'test/html-to-lexical.test.ts', 'roundtrips a product card',
                 ['roundtrips a product card with linked description and button', 'roundtrips a product card with linked description and no button'])
            ]
            for name, testfile, pattern, expected_failures in commands:
                if phase == 'lint':
                    command = [node, pnpm, 'exec', 'node', str(target / 'node_modules/eslint/bin/eslint.js'), '--no-cache']
                    if name == 'kg-default-nodes':
                        command.append('src/nodes/product/product-parser.ts')
                    command.append(testfile)
                else:
                    command = [node, pnpm, 'exec', 'vitest', 'run', '--config', 'vitest.sandbox.config.ts', '--no-coverage', '--pool=threads', '--maxWorkers=1', '--no-file-parallelism', testfile]
                    if phase == 'red':
                        command.extend(['-t', pattern, '--reporter=verbose'])
                print('RUN ' + ' '.join(command[2:]) + ' in ' + name, flush=True)
                process = subprocess.Popen(command, cwd=koenig / name, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
                try:
                    stdout, stderr = process.communicate(timeout=180)
                    code = process.returncode
                except subprocess.TimeoutExpired:
                    subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'], check=False, capture_output=True)
                    stdout, stderr = process.communicate()
                    code = 124
                    stderr += '\nTimed out after 180 seconds; process tree terminated.\n'
                print(stdout, end='')
                print(stderr, end='', file=sys.stderr)
                combined = stdout + stderr
                if phase == 'red':
                    collected = bool(code == 1 and 'AssertionError' in combined and re.search(r'Tests\s+2 failed', combined) and all(fragment in combined for fragment in expected_failures))
                elif phase == 'green':
                    collected = bool(code == 0 and re.search(r'Test Files\s+1 passed', combined) and re.search(r'Tests\s+\d+ passed', combined))
                else:
                    collected = code == 0
                results.append((name, code, collected))
                if not collected:
                    break
        finally:
            for link in reversed(links):
                if not link.is_junction() or not link.parent.resolve().is_relative_to(target):
                    raise RuntimeError(f'Unexpected link during cleanup: {link}')
                os.rmdir(link)
finally:
    print(f'SANDBOX_REMOVED={target is not None and not target.exists()}', flush=True)
print(f'PHASE={phase} RESULTS={results}', flush=True)
raise SystemExit(0 if len(results) == 2 and all(collected for _, _, collected in results) else 1)
```
<!-- END RUNNER -->
