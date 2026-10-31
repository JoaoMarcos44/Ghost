# Paginação do helper `get` — evidência

## Comportamento e correção

O helper reescrevia `id:-<id>` como `id:-null`, aumentava o limite e
filtrava os resultados localmente. O deslocamento da página passava a usar
outro limite, os totais incluíam o post excluído e uma seleção sem `id` não
podia removê-lo. A correção encaminha filtro e limite originais à API e
converte filtros `SafeString` em texto. A deduplicação de consultas idênticas
durante a mesma requisição permanece ativa.

## Resultados observados

- **RED:** `pnpm exec vitest run test/unit/frontend/helpers/get.test.ts --pool=threads --maxWorkers=1 --no-file-parallelism --testNamePattern "pagination with excluded post IDs"` retornou 1: os nove casos novos falharam pelo defeito esperado (54 testes não selecionados). Na página 2, o resultado foi `post5, post6, post7` em vez de `post4, post5, post6`; o total foi 10 em vez de 9; uma seleção sem `id` incluiu o post excluído.
- **Primeiro GREEN:** `pnpm exec vitest run test/unit/frontend/helpers/get.test.ts --pool=threads --maxWorkers=1 --no-file-parallelism` retornou 1: 58 testes passaram, incluindo os nove casos novos, e o teste preexistente `general error handling > should handle error from the API` excedeu o timeout padrão de 5000 ms. A repetição usa 15000 ms para a inicialização do Core.
- **GREEN:** `pnpm exec vitest run test/unit/frontend/helpers/get.test.ts --pool=threads --maxWorkers=1 --no-file-parallelism --testTimeout=15000` retornou 0, com **59 testes aprovados**.
- **Lint:** `pnpm exec eslint core/frontend/helpers/get.js test/unit/frontend/helpers/get.test.ts test/e2e-frontend/helpers/get.test.js` retornou 0 no mesmo sandbox do GREEN.
- `git diff --check` retornou 0 na worktree.
- Node v22.23.4, Vitest v4.1.12, um worker, heap de 4096 MB e `NX_DAEMON=false`. Cada execução confirmou `SANDBOX_CLEANUP True`.

## Limites e riscos pendentes

Os testes unitários simulam a fronteira da API com uma coleção paginada; não
executam o controller real ou MySQL. O teste E2E de paginação e os testes E2E
existentes, ajustados para verificar comportamento, não foram executados nesta
rodada. `pnpm check` completo e o hook ficam para a validação do orquestrador.

A remoção da normalização de IDs também remove o compartilhamento de uma mesma
chave de cache de API entre consultas que diferem apenas pelo ID excluído.
Consultas idênticas na mesma requisição continuam deduplicadas. Não houve
benchmark do impacto de desempenho.

## Runner

O runner abaixo cria um sandbox descartável a partir do `HEAD` da worktree,
sobrepõe os arquivos modificados e reutiliza as dependências instaladas por junções.
No modo `red`, seleciona os novos casos; no modo `green`, executa o arquivo
unitário completo e, se ele passar, o lint dos três arquivos. O runner usa
timeout de 15 segundos; a primeira execução RED acima usou o padrão de 5
segundos. A configuração de cache e as variáveis temporárias apontam
para o sandbox. Os processos são limitados a um worker e 4 GB de heap.

```powershell
$env:PAGINATION_MODE = 'red' # ou 'green'
python -c "from pathlib import Path; p=Path(r'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31-followup\pagination\results.md'); s=p.read_text(encoding='utf-8'); exec(s.split('~~~python\n',1)[1].split('\n~~~',1)[0], {'__name__':'__main__'})"
```

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

root = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-get-helper-pagination-20261031').resolve(strict=True)
mode = os.environ.get('PAGINATION_MODE', 'green')
if mode not in ('red', 'green'):
    raise RuntimeError(f'Unexpected mode: {mode}')
files = [
    'ghost/core/frontend/helpers/get.js',
    'ghost/test/unit/frontend/helpers/get.test.ts',
    'ghost/test/e2e-frontend/helpers/get.test.js',
]
status = None
sandbox = None
try:
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-pagination-', dir=root) as name:
        sandbox = Path(name).resolve(strict=True)
        if sandbox.parent != root or not sandbox.name.startswith('.tmp-sandbox-pagination-'):
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
        for part in ('node_modules', 'ghost/node_modules'):
            result = subprocess.run(
                ['cmd.exe', '/d', '/c', 'mklink', '/J', str(workspace / part), str(root / part)],
                capture_output=True, text=True,
            )
            if result.returncode:
                raise RuntimeError(f'Junction failed: {part}: {result.stderr}')

        config = workspace / 'ghost/vitest.config.ts'
        source = config.read_text(encoding='utf-8')
        source = source.replace('export default defineConfig({', "export default defineConfig({\n  cacheDir: path.join(process.env.TEMP!, 'vite-core'),", 1)
        source = source.replace('        ssr: { resolve:', "        cacheDir: path.join(process.env.TEMP!, 'vite-core-project'),\n        ssr: { resolve:", 1)
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
        node = root / 'node_modules/.bin/node.exe'
        node_version = subprocess.run([str(node), '--version'], capture_output=True, text=True, check=True).stdout.strip()
        print('NODE_VERSION', node_version, flush=True)
        if node_version != 'v22.23.4':
            raise RuntimeError(f'Unexpected Node version: {node_version}')
        pnpm = r'C:\Users\Nitro\AppData\Roaming\npm\pnpm.cmd'
        cmd = [pnpm, 'exec', 'vitest', 'run', 'test/unit/frontend/helpers/get.test.ts',
               '--pool=threads', '--maxWorkers=1', '--no-file-parallelism', '--testTimeout=15000']
        if mode == 'red':
            cmd.extend(['--testNamePattern', 'pagination with excluded post IDs'])
        print('RUN', mode, ' '.join(cmd[1:]), flush=True)
        process = subprocess.Popen(cmd, cwd=workspace / 'ghost', env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        unexpected_install = threading.Event()
        def stream():
            with (sandbox / 'vitest.log').open('w', encoding='utf-8') as log:
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
            status = process.wait(timeout=240)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process.wait()
            status = 124
        reader.join(timeout=10)
        if unexpected_install.is_set():
            raise RuntimeError('pnpm attempted an unexpected installation')
        print('EXIT', mode, status, flush=True)
        if mode == 'green' and status == 0:
            lint = [pnpm, 'exec', 'eslint', 'core/frontend/helpers/get.js',
                    'test/unit/frontend/helpers/get.test.ts', 'test/e2e-frontend/helpers/get.test.js']
            print('RUN lint', ' '.join(lint[1:]), flush=True)
            process = subprocess.Popen(lint, cwd=workspace / 'ghost', env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace')
            try:
                output, _ = process.communicate(timeout=120)
                status = process.returncode
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                output, _ = process.communicate()
                status = 124
            print(output, end='', flush=True)
            print('EXIT lint', status, flush=True)
finally:
    print('SANDBOX_CLEANUP', sandbox is not None and not sandbox.exists(), flush=True)

sys.exit(status if status is not None else 1)
~~~
