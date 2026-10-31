# Toggle HTML — evidência de implementação

**GREEN nos arquivos afetados:** `kg-default-nodes/test/nodes/toggle.test.ts` passou 16/16 testes e `kg-html-to-lexical/test/html-to-lexical.test.ts` passou 37/37; cada comando Vitest retornou exit 0. O RED havia sido comprovado nas novas asserções antes da alteração. O parser agora usa `innerHTML` para heading e content, preservando HTML rico e entidades. O worktree usa a branch `fix/toggle-html-roundtrip-20261031` na base `5d4430c8c157990adbd69400f4cee9795037fbbb`.

Foram modificados `koenig/kg-default-nodes/src/nodes/toggle/toggle-parser.ts`, os dois arquivos de teste acima e `.changeset/restore-toggle-html.md`, que declara patch apenas para `@tryghost/kg-default-nodes`. Nenhum commit foi criado. `git diff --check` retornou exit 0.

Os comandos GREEN foram executados em sandbox com Node 22.23.4, Vitest 4.1.12, dependências do próprio worktree, um worker, heap máximo de 4096 MB e `NX_DAEMON=false`:

~~~text
pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism test/nodes/toggle.test.ts
pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism test/html-to-lexical.test.ts
~~~

O wrapper dessa rodada GREEN retornou exit 1 incorretamente por exigir o caminho do arquivo na saída resumida, embora ambos os processos Vitest tenham retornado 0 e informado `Test Files 1 passed`, com 16 e 37 testes aprovados. O critério do wrapper abaixo foi corrigido para reconhecer o resumo; essa revisão do wrapper não foi executada novamente. O sandbox GREEN `.tmp-sandbox-toggle-3u77kq3n` foi removido. A suíte ampla não foi concluída: foi interrompida a pedido do orquestrador por custo, conforme histórico abaixo; não há resultado de suíte completa nem de lint nesta rodada.

## Histórico de diagnóstico

O executor abaixo foi invocado duas vezes em modo `TOGGLE_PHASE=red`, extraindo seu bloco Python deste documento e executando-o via `python -`. Os comandos internos foram:

~~~text
pnpm exec vitest run test/nodes/toggle.test.ts --config vitest.sandbox.config.ts --no-coverage --maxWorkers=1 --no-file-parallelism -t 'preserves rich heading and content|preserves escaped characters'
pnpm exec vitest run test/html-to-lexical.test.ts --config vitest.sandbox.config.ts --no-coverage --maxWorkers=1 --no-file-parallelism -t 'keeps plain toggle|preserves rich toggle'
~~~

1. Na primeira tentativa, o primeiro Vitest terminou, mas o Python falhou ao imprimir a saída com `UnicodeEncodeError: 'charmap' codec can't encode character '\\u276f'`. O launcher retornou exit 1 e não revelou a causa do resultado do Vitest. O sandbox foi removido.
2. Após ajustar somente o tratamento de caracteres do launcher, a segunda tentativa mostrou que **nenhum teste foi coletado** em ambos os pacotes: `Failed to resolve entry for package "@tryghost/kg-clean-basic-html"`. Cada Vitest retornou exit 1. O wrapper retornou exit 0 por aceitar qualquer exit 1 como RED: **esse exit 0 é falso positivo**, não prova da regressão. O sandbox foi removido.

Como a primeira saída não revelou a falha subjacente e a segunda falhou na mesma suíte antes das asserções, a execução foi interrompida para não arriscar uma terceira rodada sobre o mesmo problema. Também foi observado que o `pnpm exec` tentou verificar e instalar dependências no sandbox, abortando com `ERR_PNPM_CATALOG_ENTRY_NOT_FOUND_FOR_SPEC`; não houve instalação concluída.

A dependência `@tryghost/kg-clean-basic-html` está vinculada ao pacote workspace correto e seu `src/index.ts` existe, mas os arquivos `build/esm/index.js` e `build/cjs/index.js` estão ausentes. A hipótese é que a resolução SSR do Vitest não recebeu a condição `source` esperada para o pacote. O launcher também precisa desativar a verificação automática de dependências do pnpm no sandbox e distinguir falhas de setup de falhas de asserção antes de ser considerado evidência.

Ambos os processos terminaram e os sandboxes `.tmp-sandbox-toggle-azmbad3g` e `.tmp-sandbox-toggle-z1j28ulm` foram removidos.

Após o diagnóstico do orquestrador, uma nova execução copiou as seis dependências workspace Koenig ao sandbox e criou aliases para todos os exports `source`, com `pnpm_config_verify_deps_before_run=false`. O RED ficou comprovado: em `kg-default-nodes`, os dois testes novos falharam nas asserções de formatação e entidades; em `kg-html-to-lexical`, o teste rico falhou na asserção e o controle plain passou. Cada Vitest retornou exit 1; o executor retornou exit 0 após conferir que as falhas eram as asserções esperadas. O sandbox `.tmp-sandbox-toggle-qvlgtbz2` foi removido.

Foi aplicada a troca de `textContent` por `innerHTML` nos campos de heading e content. A tentativa de rodar as duas suítes completas foi interrompida por decisão do orquestrador, por custo: o processo do primeiro Vitest foi encerrado e o segundo comando abortou antes de coletar testes. O executor então retornou exit 1 e removeu `.tmp-sandbox-toggle-83ngkq32`. Não interprete essa interrupção como falha das asserções. A execução seguinte cobriu os dois arquivos afetados completos, como descrito no início.

## Executor isolado atualizado

Para repetir o GREEN, defina `TOGGLE_PHASE=green` e execute o bloco Python abaixo via `python -`. O modo RED só é válido antes de aplicar a correção. O executor copia o código para sandbox, cria aliases para os exports `source` dos pacotes Koenig envolvidos e remove as junctions e o sandbox ao terminar. O critério atualizado de coleta do GREEN ainda não foi executado.

~~~powershell
$env:TOGGLE_PHASE = 'green'
$report = Get-Content -LiteralPath 'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31\toggle\evidence.md' -Raw -Encoding UTF8
$match = [regex]::Match($report, '(?s)<!-- BEGIN RUNNER -->\s*```python\s*\n(.*?)\n```\s*<!-- END RUNNER -->')
if (-not $match.Success) { throw 'Runner not found' }
$match.Groups[1].Value | python -
exit $LASTEXITCODE
~~~

<!-- BEGIN RUNNER -->
```python
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile

sys.stdout.reconfigure(errors='backslashreplace')
sys.stderr.reconfigure(errors='backslashreplace')
repo = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-toggle-html-roundtrip-20261031').resolve(strict=True)
node = r'C:\Users\Nitro\ghost-functional-audit\source\node_modules\.bin\node.exe'
pnpm = r'C:\Users\Nitro\AppData\Roaming\npm\node_modules\pnpm\bin\pnpm.cjs'
phase = os.environ.get('TOGGLE_PHASE', 'red')
if phase not in ('red', 'green'):
    raise SystemExit('TOGGLE_PHASE must be red or green')
for name in ('node_modules', 'koenig/kg-default-nodes/node_modules', 'koenig/kg-html-to-lexical/node_modules'):
    if not (repo / name).is_dir():
        raise SystemExit(f'Bootstrap dependency missing: {repo / name}')
env = os.environ.copy()
env.update(NODE_OPTIONS='--max-old-space-size=4096 --conditions=source', UV_THREADPOOL_SIZE='1', NX_DAEMON='false', CI='true', pnpm_config_verify_deps_before_run='false')
env['PATH'] = str(Path(node).parent) + os.pathsep + env['PATH']
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
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-toggle-', dir=str(repo)) as temporary:
        target = Path(temporary).resolve(strict=True)
        if target.parent != repo or not target.name.startswith('.tmp-sandbox-toggle-') or target.is_symlink():
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
                ('kg-default-nodes', 'test/nodes/toggle.test.ts', 'preserves rich heading and content|preserves escaped characters'),
                ('kg-html-to-lexical', 'test/html-to-lexical.test.ts', 'keeps plain toggle|preserves rich toggle')
            ]
            for name, testfile, pattern in commands:
                command = [node, pnpm, 'exec', 'vitest', 'run', '--config', 'vitest.sandbox.config.ts', '--no-coverage', '--pool=threads', '--maxWorkers=1', '--no-file-parallelism']
                command.append(testfile)
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
                expected_failures = ['preserves rich heading and content', 'preserves escaped characters'] if name == 'kg-default-nodes' else ['preserves rich toggle HTML', 'keeps plain toggle']
                collected = ('AssertionError' in combined and all(fragment in combined for fragment in expected_failures)) if phase == 'red' else bool(re.search(r'Test Files\s+1 passed', combined) and re.search(r'Tests\s+\d+ passed', combined))
                results.append((name, code, collected))
        finally:
            for link in reversed(links):
                if not link.is_junction() or not link.parent.resolve().is_relative_to(target):
                    raise RuntimeError(f'Unexpected link during cleanup: {link}')
                os.rmdir(link)
finally:
    print(f'SANDBOX_REMOVED={target is not None and not target.exists()}', flush=True)
print(f'PHASE={phase} RESULTS={results}', flush=True)
if len(results) != 2:
    raise SystemExit(2)
if phase == 'red':
    raise SystemExit(0 if all(code == 1 and collected for _, code, collected in results) else 1)
raise SystemExit(0 if all(code == 0 and collected for _, code, collected in results) else 1)
```
<!-- END RUNNER -->

## Commit e publicação

Commit `af654561e2f883f086fd694abede433abfffff6b`, PR https://github.com/TryGhost/Ghost/pull/32432 (draft).

Os hooks de commit passaram: formatação, ESLint dos dois pacotes, inspeção de arquivos staged e validação do changeset. O formatter ajustou somente o teste do conversor e a apresentação do changeset; o parser mantém a alteração de dois campos. O teste do conversor apontado pelo check focado foi formatado pelo hook. O check global continuou pendente após interromper na formatação de milhares de arquivos fora da mudança; não há alegação de suíte completa aprovada.
