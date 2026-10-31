# Validação isolada da correção de labels

O comando abaixo executa a aceitação do Admin na versão atual do worktree.
Ele arquiva o commit-base, sobrepõe os arquivos alterados, usa as dependências
existentes em modo de leitura e instala somente o Chromium headless do
Playwright dentro do sandbox temporário. O alias de Admin Framework aponta para
a cópia no sandbox. A suíte usa Node 22.23.4, um worker e limite de heap de 4 GB.
Os testes MySQL não estão incluídos porque não havia engine local disponível.

```powershell
$env:LABEL_ACCEPTANCE_WITH_BROWSER='1'
python -c "from pathlib import Path; p=Path(r'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31\labels\reproduce.md'); s=p.read_text(encoding='utf-8'); exec(s.split('~~~python\n',1)[1].split('\n~~~',1)[0], {'__name__':'__main__'})"
```

Sem a variável `LABEL_ACCEPTANCE_WITH_BROWSER`, o runner executa os testes
unitários do Core e tenta a aceitação com o navegador disponível no ambiente.

~~~python
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

root = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-member-label-removal-20261031').resolve()
files = [
    'apps/admin-x-framework/src/api/config.ts',
    'apps/admin-x-framework/src/api/members.ts',
    'apps/admin/src/members/components/bulk-action-modals/remove-label-modal.tsx',
    'apps/admin/src/members/components/members-actions.tsx',
    'apps/admin/src/members/members-bulk-actions.acceptance.test.tsx',
    'apps/admin/src/members/members.tsx',
    'ghost/core/server/api/endpoints/members.js',
    'ghost/core/server/api/endpoints/utils/public-config/config.js',
    'ghost/core/server/api/endpoints/utils/serializers/output/config.js',
    'ghost/core/server/models/member.js',
    'ghost/core/server/services/members/members-api/repositories/member-repository.js',
    'ghost/test/e2e-api/admin/__snapshots__/config.test.js.snap',
    'ghost/test/e2e-api/admin/config.test.js',
    'ghost/test/e2e-api/admin/members.test.js',
    'ghost/test/unit/server/api/endpoints/utils/public-config/config.test.js',
    'ghost/test/unit/server/services/members/members-api/repositories/member-repository.test.js',
]
status = {}
sandbox = None
browser_mode = os.environ.get('LABEL_ACCEPTANCE_WITH_BROWSER') == '1'

try:
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-label-suites-', dir=root) as name:
        sandbox = Path(name).resolve()
        if sandbox.parent != root or not sandbox.name.startswith('.tmp-sandbox-label-suites-'):
            raise RuntimeError(f'Unexpected sandbox path: {sandbox}')
        workspace = sandbox / 'source'
        workspace.mkdir()
        temp = sandbox / 'temp'
        temp.mkdir()
        archive = sandbox / 'source.tar'
        with archive.open('wb') as out:
            subprocess.run(['git', 'archive', '--format=tar', 'HEAD'], cwd=root, stdout=out, check=True, timeout=120)
        with tarfile.open(archive) as tf:
            tf.extractall(workspace, members=(m for m in tf if m.isfile() or m.isdir()), filter='data')
        archive.unlink()
        for item in files:
            shutil.copyfile(root / item, workspace / item)
        for part in ['node_modules', 'ghost/node_modules', 'apps/admin/node_modules', 'apps/admin-x-framework/node_modules']:
            result = subprocess.run(
                ['cmd.exe', '/d', '/c', 'mklink', '/J', str(workspace / part), str(root / part)],
                capture_output=True, text=True,
            )
            if result.returncode:
                raise RuntimeError(f'Junction failed: {part}: {result.stderr}')

        core_config = workspace / 'ghost/vitest.config.ts'
        source = core_config.read_text(encoding='utf-8')
        source = source.replace('export default defineConfig({', "export default defineConfig({\n  cacheDir: path.join(process.env.TEMP!, 'vite-core'),", 1)
        source = source.replace('        ssr: { resolve:', "        cacheDir: path.join(process.env.TEMP!, 'vite-core-project'),\n        ssr: { resolve:", 1)
        core_config.write_text(source, encoding='utf-8')
        admin_config = workspace / 'apps/admin/vitest.acceptance.config.ts'
        source = admin_config.read_text(encoding='utf-8')
        source = source.replace('export default defineConfig({', "export default defineConfig({\n  cacheDir: process.env.TEMP + '/vite-admin',", 1)
        admin_config.write_text(source, encoding='utf-8')
        shared = workspace / 'apps/admin/vite.shared.ts'
        source = shared.read_text(encoding='utf-8')
        source = source.replace('  alias: {\n', "  alias: {\n    '@tryghost/admin-x-framework': resolve(__dirname, '../admin-x-framework/src'),\n", 1)
        shared.write_text(source, encoding='utf-8')

        env = os.environ.copy()
        for key in ('TEMP', 'TMP', 'TMPDIR', 'XDG_CACHE_HOME'):
            env[key] = str(temp)
        env.update(
            NODE_OPTIONS='--max-old-space-size=4096', UV_THREADPOOL_SIZE='1',
            NX_DAEMON='false', CI='true', pnpm_config_verify_deps_before_run='false',
            NO_COLOR='1', FORCE_COLOR='0',
        )
        if browser_mode:
            env['PLAYWRIGHT_BROWSERS_PATH'] = str(sandbox / 'browsers')
        env['PATH'] = str(root / 'node_modules/.bin') + os.pathsep + env['PATH']
        node_version = subprocess.run([str(root / 'node_modules/.bin/node.exe'), '--version'],
                                      capture_output=True, text=True, check=True).stdout.strip()
        print('NODE_VERSION', node_version, flush=True)
        if node_version != 'v22.23.4':
            raise RuntimeError(f'Unexpected Node version: {node_version}')
        pnpm = r'C:\Users\Nitro\AppData\Roaming\npm\pnpm.cmd'
        suites = [
            ('core-unit', workspace / 'ghost', [pnpm, 'exec', 'vitest', 'run',
             'test/unit/server/services/members/members-api/repositories/member-repository.test.js',
             'test/unit/server/api/endpoints/utils/public-config/config.test.js',
             '--pool=threads', '--maxWorkers=1', '--no-file-parallelism']),
            ('admin-acceptance', workspace / 'apps/admin', [pnpm, 'exec', 'vitest', 'run',
             '-c', 'vitest.acceptance.config.ts', 'src/members/members-bulk-actions.acceptance.test.tsx',
             '--pool=threads', '--maxWorkers=1', '--no-file-parallelism']),
        ]
        if browser_mode:
            suites = [
                ('install-browser', workspace, [pnpm, 'exec', 'playwright',
                 'install', 'chromium', '--only-shell']),
                suites[1],
            ]
        for label, cwd, cmd in suites:
            print('RUN', label, ' '.join(cmd[1:]), flush=True)
            process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            unexpected_install = threading.Event()
            def stream():
                download_timeouts = 0
                with (sandbox / f'{label}.log').open('w', encoding='utf-8') as log:
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                        print(line, end='', flush=True)
                        if 'verify-deps-before-run-install' in line or 'preinstall$' in line:
                            unexpected_install.set()
                            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            break
                        if label == 'install-browser' and 'Error: Request to ' in line and 'timed out' in line:
                            download_timeouts += 1
                            if download_timeouts >= 2:
                                print('STOP: browser download timed out twice', flush=True)
                                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                break
            reader = threading.Thread(target=stream, daemon=True)
            reader.start()
            try:
                status[label] = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()
                status[label] = 124
            reader.join(timeout=10)
            print('EXIT', label, status[label], flush=True)
            if unexpected_install.is_set():
                print('STOP: pnpm attempted an installation', flush=True)
                break
            if label == 'install-browser' and status[label] != 0:
                print('STOP: browser installation failed', flush=True)
                break
finally:
    print('SANDBOX_CLEANUP', sandbox is not None and not sandbox.exists(), flush=True)

print('SUITE_EXITS', status, flush=True)
sys.exit(0 if len(status) == 2 and all(code == 0 for code in status.values()) else 1)
~~~
