"""Run the Core integration regression with its actual Vitest setup in a sandbox."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-toggle-html-roundtrip-20261031').resolve(strict=True)
ROOT = Path(r'C:\Users\Nitro\Ghost').resolve(strict=True)
NODE = Path(r'C:\Users\Nitro\ghost-functional-audit\source\node_modules\.bin\node.exe')
VITEST = REPO / 'node_modules/vitest/vitest.mjs'
PACKAGES = ('kg-default-nodes', 'kg-html-to-lexical', 'kg-default-transforms',
            'kg-clean-basic-html', 'kg-markdown-html-renderer', 'kg-utils',
            'kg-lexical-html-renderer')
TEST = 'test/unit/server/services/email-service/toggle-email.test.ts'

env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR', 'PATH', 'PATHEXT',
                                        'COMSPEC', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE')
       if key in os.environ}
env.update(NODE_OPTIONS='--max-old-space-size=2048 --conditions=source',
           UV_THREADPOOL_SIZE='1', RAYON_NUM_THREADS='1', NX_DAEMON='false', CI='true',
           NODE_ENV='testing', pnpm_config_verify_deps_before_run='false')
env['PATH'] = str(NODE.parent) + os.pathsep + env['PATH']
target = Path(tempfile.mkdtemp(prefix='.tmp-pr32432-core-', dir=str(ROOT))).resolve(strict=True)
if target.parent != ROOT or not target.name.startswith('.tmp-pr32432-core-'):
    raise RuntimeError('Unexpected sandbox path')
print(f'SANDBOX={target}', flush=True)
env['TEMP'] = env['TMP'] = str(target)
env['XDG_CACHE_HOME'] = str(target / '.cache')
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

    tracked = subprocess.check_output(['git', '-C', str(REPO), 'ls-files', '-z',
                                       '--', 'ghost/core', 'ghost/test/utils']).decode('utf-8').split('\0')
    for name in tracked:
        if not name:
            continue
        source = REPO / name
        dest = target / name
        if source.is_symlink() or not source.resolve(strict=True).is_relative_to(REPO):
            raise RuntimeError(f'Unexpected tracked path: {source}')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    for name in ('ghost/package.json', 'ghost/vitest.config.ts', f'ghost/{TEST}'):
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / name, dest)
    junction(target / 'ghost/node_modules', REPO / 'ghost/node_modules')
    (target / 'ghost/content').mkdir()
    env['paths__contentPath'] = str(target / 'ghost/content')
    env['database__connection__filename'] = str(target / 'ghost/test.db')

    config_path = target / 'ghost/vitest.config.ts'
    config = config_path.read_text(encoding='utf-8')
    marker = "        ssr: { resolve: { conditions: ['source', 'node'] } },"
    if config.count(marker) != 1:
        raise RuntimeError('Unexpected Core Vitest configuration')
    config = config.replace(marker,
        '        cacheDir: ' + json.dumps((target / '.vite-core').as_posix()) + ',\n'
        + '        resolve: { alias: ' + json.dumps(aliases) + ' },\n'
        + "        ssr: { noExternal: [/^@tryghost\\/kg-/], resolve: { conditions: ['source', 'node'] } },")
    marker = '          ...unitConfig,'
    if config.count(marker) != 1:
        raise RuntimeError('Unexpected Core unit configuration')
    config = config.replace(marker, marker + "\n          server: {deps: {inline: [/^@tryghost\\/kg-/]}},")
    config = config.replace('export default defineConfig({',
                            'export default defineConfig({\n  cacheDir: '
                            + json.dumps((target / '.vite').as_posix()) + ',')
    config_path.write_text(config, encoding='utf-8')

    command = [str(NODE), str(VITEST), 'run', '--config', 'vitest.config.ts', '--project', 'unit',
               '--no-coverage', '--pool=threads', '--maxWorkers=1', '--no-file-parallelism',
               '--reporter=verbose', TEST]
    print('RUN CWD=' + str(target / 'ghost') + ': ' + subprocess.list2cmdline(command), flush=True)
    process = subprocess.Popen(command, cwd=target / 'ghost', env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
    try:
        output, _ = process.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=False)
        output, _ = process.communicate()
        print(output, flush=True)
        raise RuntimeError('Core test timed out; process tree terminated')
    print(output, flush=True)
    result = process.returncode
    print(f'CORE_VITEST_EXIT={result}', flush=True)
finally:
    for link in reversed(links):
        if not link.is_junction() or not link.parent.resolve().is_relative_to(target):
            raise RuntimeError(f'Unexpected link during cleanup: {link}')
        os.rmdir(link)
    shutil.rmtree(target)
    print(f'SANDBOX_REMOVED={not target.exists()}', flush=True)

sys.exit(result if result is not None else 1)
