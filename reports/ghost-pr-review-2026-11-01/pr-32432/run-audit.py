"""Run the accompanying source-level audit in a disposable Windows sandbox."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-toggle-html-roundtrip-20261031').resolve(strict=True)
SANDBOX_ROOT = Path(r'C:\Users\Nitro\Ghost').resolve(strict=True)
REPORT = Path(__file__).resolve().parent
NODE = Path(r'C:\Users\Nitro\ghost-functional-audit\source\node_modules\.bin\node.exe')
PNPM = Path(r'C:\Users\Nitro\AppData\Roaming\npm\node_modules\pnpm\bin\pnpm.cjs')
BASE = '80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b'
HEAD = 'af654561e2f883f086fd694abede433abfffff6b'
PARSER = 'koenig/kg-default-nodes/src/nodes/toggle/toggle-parser.ts'
PACKAGES = ('kg-default-nodes', 'kg-html-to-lexical', 'kg-default-transforms',
            'kg-clean-basic-html', 'kg-markdown-html-renderer', 'kg-utils',
            'kg-lexical-html-renderer')

if subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() != HEAD:
    raise RuntimeError('The worktree is not on the audited head')

env = os.environ.copy()
env.update(NODE_OPTIONS='--max-old-space-size=2048 --conditions=source',
           UV_THREADPOOL_SIZE='1', NX_DAEMON='false', CI='true',
           pnpm_config_verify_deps_before_run='false')
env['PATH'] = str(NODE.parent) + os.pathsep + env['PATH']
links = []
target = None
results = []

def junction(link, destination):
    link_env = env.copy()
    link_env['TOGGLE_JUNCTION_LINK'] = str(link)
    link_env['TOGGLE_JUNCTION_TARGET'] = str(destination)
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                    'New-Item -ItemType Junction -Path $env:TOGGLE_JUNCTION_LINK -Target $env:TOGGLE_JUNCTION_TARGET -ErrorAction Stop | Out-Null'],
                   env=link_env, check=True)
    links.append(link)

try:
    with tempfile.TemporaryDirectory(prefix='.tmp-pr32432-audit-', dir=str(SANDBOX_ROOT)) as temporary:
        target = Path(temporary).resolve(strict=True)
        if target.parent != SANDBOX_ROOT or not target.name.startswith('.tmp-pr32432-audit-'):
            raise RuntimeError('Unexpected sandbox path')
        print(f'SANDBOX={target}', flush=True)
        env['TEMP'] = env['TMP'] = str(target)
        env['XDG_CACHE_HOME'] = str(target / '.cache')
        env['NPM_CONFIG_USERCONFIG'] = str(target / 'npm-user-empty')
        env['NPM_CONFIG_GLOBALCONFIG'] = str(target / 'npm-global-empty')
        try:
            junction(target / 'node_modules', REPO / 'node_modules')
            aliases = []
            for name in PACKAGES:
                source = REPO / 'koenig' / name
                dest = target / 'koenig' / name
                dest.mkdir(parents=True)
                shutil.copytree(source / 'src', dest / 'src')
                shutil.copy2(source / 'package.json', dest / 'package.json')
                junction(dest / 'node_modules', source / 'node_modules')
                package = json.loads((dest / 'package.json').read_text(encoding='utf-8'))
                for subpath, condition in package.get('exports', {}).items():
                    if isinstance(condition, dict) and 'source' in condition:
                        module = package['name'] + ('' if subpath == '.' else subpath[1:])
                        aliases.append({'find': module, 'replacement': (dest / condition['source']).as_posix()})
            aliases.sort(key=lambda item: len(item['find']), reverse=True)
            package_dir = target / 'koenig' / 'kg-html-to-lexical'
            (package_dir / 'test').mkdir()
            shutil.copy2(REPORT / 'audit-toggle.test.ts', package_dir / 'test' / 'audit-toggle.test.ts')
            shutil.copy2(REPORT / 'audit-editor.test.ts', package_dir / 'test' / 'audit-editor.test.ts')
            helpers = package_dir / 'test' / 'editor-helpers'
            helpers.mkdir()
            editor_src = REPO / 'koenig' / 'koenig-lexical' / 'src'
            shutil.copy2(editor_src / 'utils' / 'generateEditorState.ts', helpers / 'generateEditorState.ts')
            shutil.copy2(editor_src / 'nodes' / 'BasicNodes.ts', helpers / 'BasicNodes.ts')
            shutil.copy2(editor_src / 'nodes' / 'MinimalNodes.ts', helpers / 'MinimalNodes.ts')
            config = ("import {defineConfig} from 'vitest/config';\n"
                      + 'export default defineConfig({cacheDir: ' + json.dumps((target / '.vite').as_posix())
                      + ', resolve: {alias: ' + json.dumps(aliases)
                      + ", conditions: ['source', 'node']}, test: {environment: 'node', server: {deps: {inline: [/^@tryghost\\/kg-/]}}}});\n")
            (package_dir / 'vitest.sandbox.config.ts').write_text(config, encoding='utf-8')
            parser = target / PARSER
            head_parser = parser.read_bytes()
            base_parser = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{BASE}:{PARSER}'])
            for phase, source in (('base', base_parser), ('head', head_parser)):
                parser.write_bytes(source)
                env['TOGGLE_AUDIT_PHASE'] = phase
                cmd = [str(NODE), str(PNPM), 'exec', 'vitest', 'run', '--config',
                       'vitest.sandbox.config.ts', '--no-coverage', '--pool=threads',
                       '--maxWorkers=1', '--no-file-parallelism', '--reporter=verbose',
                       'test/audit-toggle.test.ts', 'test/audit-editor.test.ts']
                print(f'RUN phase={phase}: pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose test/audit-toggle.test.ts test/audit-editor.test.ts', flush=True)
                process = subprocess.Popen(cmd, cwd=package_dir, env=env, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                try:
                    output, _ = process.communicate(timeout=180)
                except subprocess.TimeoutExpired:
                    subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False)
                    output, _ = process.communicate()
                    print(output, flush=True)
                    raise RuntimeError(f'{phase} timed out; process tree terminated')
                print(output, flush=True)
                results.append((phase, process.returncode))
                if process.returncode:
                    break
        finally:
            for link in reversed(links):
                if not link.is_junction() or not link.parent.resolve().is_relative_to(target):
                    raise RuntimeError(f'Unexpected link during cleanup: {link}')
                os.rmdir(link)
finally:
    print(f'SANDBOX_REMOVED={target is not None and not target.exists()}', flush=True)

print(f'RESULTS={results}', flush=True)
sys.exit(0 if results == [('base', 0), ('head', 0)] else 1)
