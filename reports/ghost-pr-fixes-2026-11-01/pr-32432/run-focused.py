"""Run the upstream toggle regressions against disposable copies of the source."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-toggle-html-roundtrip-20261031').resolve(strict=True)
ROOT = Path(r'C:\Users\Nitro\Ghost').resolve(strict=True)
NODE = REPO / 'node_modules/.bin/node.exe'
VITEST = REPO / 'node_modules' / 'vitest' / 'vitest.mjs'
PACKAGES = ('kg-default-nodes', 'kg-html-to-lexical', 'kg-default-transforms',
            'kg-clean-basic-html', 'kg-markdown-html-renderer', 'kg-utils',
            'kg-lexical-html-renderer')
TESTS = ('koenig/kg-default-nodes/test/nodes/toggle.test.ts',
         'koenig/kg-html-to-lexical/test/html-to-lexical.test.ts',
         'ghost/test/unit/server/services/email-service/toggle-email.test.ts')

env = os.environ.copy()
env.update(NODE_OPTIONS='--max-old-space-size=2048 --conditions=source',
           UV_THREADPOOL_SIZE='1', RAYON_NUM_THREADS='1', NX_DAEMON='false', CI='true', NODE_ENV='testing',
           pnpm_config_verify_deps_before_run='false')
env['PATH'] = str(NODE.parent) + os.pathsep + env['PATH']
target = Path(tempfile.mkdtemp(prefix='.tmp-pr32432-fix-', dir=str(ROOT))).resolve(strict=True)
if target.parent != ROOT or not target.name.startswith('.tmp-pr32432-fix-'):
    raise RuntimeError('Unexpected sandbox path')
print(f'SANDBOX={target}', flush=True)
env['TEMP'] = env['TMP'] = str(target)
env['XDG_CACHE_HOME'] = str(target / '.cache')
env['NPM_CONFIG_USERCONFIG'] = str(target / 'npm-user-empty')
env['NPM_CONFIG_GLOBALCONFIG'] = str(target / 'npm-global-empty')
links = []
result = None


def junction(link, destination):
    link_env = env.copy()
    link_env['TOGGLE_JUNCTION_LINK'] = str(link)
    link_env['TOGGLE_JUNCTION_TARGET'] = str(destination)
    subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                    'New-Item -ItemType Junction -Path $env:TOGGLE_JUNCTION_LINK -Target $env:TOGGLE_JUNCTION_TARGET -ErrorAction Stop | Out-Null'],
                   env=link_env, check=True)
    links.append(link)


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

    shutil.copytree(REPO / 'koenig/kg-default-nodes/test/test-utils',
                    target / 'koenig/kg-default-nodes/test/test-utils')
    for test in TESTS:
        destination = target / test
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / test, destination)
    junction(target / 'ghost/node_modules', REPO / 'ghost/node_modules')
    for config_path in ('koenig/kg-default-nodes/eslint.config.mjs',
                        'ghost/eslint.config.mjs', '.oxfmtrc.json'):
        shutil.copy2(REPO / config_path, target / config_path)

    renderer_path = 'koenig/kg-default-nodes/src/nodes/toggle/toggle-renderer.ts'
    original_renderer = subprocess.check_output(['git', '-C', str(REPO), 'show', f'af654561e2f883f086fd694abede433abfffff6b:{renderer_path}'])
    (target / 'koenig/kg-default-nodes/src/nodes/toggle/toggle-renderer-before.ts').write_bytes(original_renderer)
    comparison = target / 'koenig/kg-default-nodes/test/toggle-structural.test.ts'
    comparison.write_text("""import {JSDOM} from 'jsdom';
import {renderToggleNode as before} from '../src/nodes/toggle/toggle-renderer-before.js';
import {renderToggleNode as after} from '../src/nodes/toggle/toggle-renderer.js';

test('keeps exact email HTML for cases unaffected by inline spacing', () => {
    const dom = new JSDOM();
    try {
        for (const node of [
            {heading: 'Heading', content: 'Content'},
            {heading: '', content: ''},
            {heading: 'Read <em>more</em>', content: '<p>Read <strong>this</strong> today</p>'}
        ]) {
            expect(after(node, {dom, target: 'email'}).element.outerHTML)
                .toBe(before(node, {dom, target: 'email'}).element.outerHTML);
        }
    } finally {
        dom.window.close();
    }
});
""", encoding='utf-8')

    config = ("import {defineConfig} from 'vitest/config';\n"
              + 'export default defineConfig({cacheDir: ' + json.dumps((target / '.vite').as_posix())
              + ', resolve: {alias: ' + json.dumps(aliases)
              + ", conditions: ['source', 'node']}, test: {globals: true, environment: 'node', server: {deps: {inline: [/^@tryghost\\/kg-/]}}}});\n")
    (target / 'vitest.sandbox.config.ts').write_text(config, encoding='utf-8')
    commands = [
        ('vitest', target, [str(NODE), str(VITEST), 'run', '--config', 'vitest.sandbox.config.ts',
                            '--no-coverage', '--pool=threads', '--maxWorkers=1', '--no-file-parallelism',
                            '--reporter=verbose', *TESTS,
                            *([comparison.relative_to(target).as_posix()] if '--compare-baseline' in sys.argv else [])]),
        ('eslint-node', target / 'koenig/kg-default-nodes',
         [str(NODE), str(REPO / 'node_modules/eslint/bin/eslint.js'),
          'src/nodes/toggle/toggle-renderer.ts', 'test/nodes/toggle.test.ts']),
        ('eslint-ghost', target / 'ghost',
         [str(NODE), str(REPO / 'node_modules/eslint/bin/eslint.js'),
          'test/unit/server/services/email-service/toggle-email.test.ts']),
        ('oxfmt', target, [str(NODE), str(REPO / 'node_modules/oxfmt/bin/oxfmt'), '--check', '--threads=1',
                            'ghost/test/unit/server/services/email-service/toggle-email.test.ts'])
    ]
    result = 0
    for label, cwd, command in commands:
        print(f'RUN {label} CWD={cwd}: ' + subprocess.list2cmdline(command), flush=True)
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        try:
            output, _ = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False)
            output, _ = process.communicate()
            print(output, flush=True)
            raise RuntimeError(f'{label} timed out; process tree terminated')
        print(output, flush=True)
        print(f'{label.upper()}_EXIT={process.returncode}', flush=True)
        if process.returncode:
            result = process.returncode
finally:
    for link in reversed(links):
        if not link.is_junction() or not link.parent.resolve().is_relative_to(target):
            raise RuntimeError(f'Unexpected link during cleanup: {link}')
        os.rmdir(link)
    shutil.rmtree(target)
    print(f'SANDBOX_REMOVED={not target.exists()}', flush=True)

sys.exit(result if result is not None else 1)
