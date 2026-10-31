from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading


sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['red', 'green'])
phase = parser.parse_args().phase

root = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-subscriber-history-anchor-20261031').resolve()
pnpm = r'C:\Users\Nitro\AppData\Roaming\npm\pnpm.cmd'
test_file = 'ghost/test/unit/server/services/stats/posts.test.js'
service_file = 'ghost/core/server/services/stats/posts-stats-service.js'
sandbox = None
exit_code = 1

try:
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-history-', dir=root) as name:
        sandbox = Path(name).resolve()
        if sandbox.parent != root or not sandbox.name.startswith('.tmp-sandbox-history-'):
            raise RuntimeError(f'Unexpected sandbox path: {sandbox}')
        workspace = sandbox / 'source'
        workspace.mkdir()
        temp = sandbox / 'temp'
        temp.mkdir()
        archive = sandbox / 'source.tar'
        with archive.open('wb') as out:
            subprocess.run(['git', 'archive', '--format=tar', 'HEAD'], cwd=root,
                           stdout=out, check=True, timeout=120)
        with tarfile.open(archive) as tf:
            tf.extractall(workspace, members=(m for m in tf if m.isfile() or m.isdir()), filter='data')
        archive.unlink()

        for item in [test_file] + ([service_file] if phase == 'green' else []):
            shutil.copyfile(root / item, workspace / item)

        junctions = []
        try:
            for part in ['node_modules', 'ghost/node_modules']:
                destination = workspace / part
                result = subprocess.run(
                    ['cmd.exe', '/d', '/c', 'mklink', '/J', str(destination), str(root / part)],
                    capture_output=True, text=True,
                )
                if result.returncode:
                    raise RuntimeError(f'Junction failed: {part}: {result.stderr}')
                junctions.append(destination)

            config = workspace / 'ghost/vitest.config.ts'
            source = config.read_text(encoding='utf-8')
            source = source.replace(
                'export default defineConfig({',
                "export default defineConfig({\n  cacheDir: path.join(process.env.TEMP!, 'vite-core'),",
                1,
            )
            source = source.replace(
                '        ssr: { resolve:',
                "        cacheDir: path.join(process.env.TEMP!, 'vite-core-project'),\n        ssr: { resolve:",
                1,
            )
            config.write_text(source, encoding='utf-8')

            env = os.environ.copy()
            for key in ('TEMP', 'TMP', 'TMPDIR', 'XDG_CACHE_HOME'):
                env[key] = str(temp)
            env.update(
                NODE_OPTIONS='--max-old-space-size=4096', UV_THREADPOOL_SIZE='1',
                NX_DAEMON='false', CI='true', pnpm_config_verify_deps_before_run='false',
                NO_COLOR='1', FORCE_COLOR='0',
            )
            env['PATH'] = str(root / 'node_modules/.bin') + os.pathsep + env['PATH']
            node_version = subprocess.run([str(root / 'node_modules/.bin/node.exe'), '--version'],
                                          env=env, capture_output=True, text=True, check=True).stdout.strip()
            print('NODE_VERSION', node_version, flush=True)
            if node_version != 'v22.23.4':
                raise RuntimeError(f'Unexpected Node version: {node_version}')

            cmd = [pnpm, 'exec', 'vitest', 'run', 'test/unit/server/services/stats/posts.test.js',
                   '--pool=threads', '--maxWorkers=1', '--no-file-parallelism']
            if phase == 'red':
                cmd.extend(['-t', 'getNewsletterSubscriberStats'])
            print('RUN', phase, ' '.join(cmd[1:]), flush=True)
            process = subprocess.Popen(cmd, cwd=workspace / 'ghost', env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace')
            unexpected_install = threading.Event()

            def stream():
                with (sandbox / f'{phase}.log').open('w', encoding='utf-8') as log:
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                        print(line, end='', flush=True)
                        if 'verify-deps-before-run-install' in line or 'preinstall$' in line:
                            unexpected_install.set()
                            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            break

            reader = threading.Thread(target=stream, daemon=True)
            reader.start()
            try:
                exit_code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.wait()
                exit_code = 124
            reader.join(timeout=10)
            if unexpected_install.is_set():
                print('STOP: pnpm attempted an installation', flush=True)
                exit_code = 1
            print('TEST_EXIT', exit_code, flush=True)
        finally:
            for junction in reversed(junctions):
                os.rmdir(junction)
finally:
    print('SANDBOX_CLEANUP', sandbox is not None and not sandbox.exists(), flush=True)

sys.exit(exit_code)
