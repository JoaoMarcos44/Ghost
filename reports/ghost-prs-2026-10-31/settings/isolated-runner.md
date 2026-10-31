# Validação isolada da correção de salvamento de configurações

O bloco abaixo copia o hook, o grupo, os testes upstream e o contexto para um
sandbox temporário dentro da worktree, usa dependências instaladas em modo
somente leitura e remove o sandbox ao sair. Os resultados reais são registrados
separadamente.

~~~powershell
python -c "from pathlib import Path; import sys; p=Path(r'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31\settings\isolated-runner.md'); s=p.read_text(encoding='utf-8'); exec(s.split('~~~python\n',1)[1].split('\n~~~',1)[0], {'__name__':'__main__'})"
~~~

~~~python
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

root = Path(r'C:\Users\Nitro\Ghost\.worktrees\fix-settings-pending-save-20261031').resolve()
node = root / 'node_modules/.bin/node.exe'
deps = root / 'apps/admin/node_modules'
files = [
    'apps/admin-x-framework/src/hooks/use-form.ts',
    'apps/admin-x-framework/test/unit/hooks/use-form.test.ts',
    'apps/admin/src/settings/hooks/use-setting-group.tsx',
    'apps/admin/src/settings/hooks/use-setting-group.test.tsx',
    'apps/admin/src/settings/providers/global-data-context.ts',
]
config = r"""
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031/apps/admin/node_modules';
const local = name => path.join(root, name);
export default {
  root,
  cacheDir: local('.vite-cache'),
  resolve: {alias: [
    {find: /^react$/, replacement: deps + '/react/index.js'},
    {find: /^react\/jsx-dev-runtime$/, replacement: deps + '/react/jsx-dev-runtime.js'},
    {find: /^react\/jsx-runtime$/, replacement: deps + '/react/jsx-runtime.js'},
    {find: /^react-dom$/, replacement: deps + '/react-dom/index.js'},
    {find: /^react-dom\/client$/, replacement: deps + '/react-dom/client.js'},
    {find: /^react-dom\/test-utils$/, replacement: deps + '/react-dom/test-utils.js'},
    {find: /^@testing-library\/react$/, replacement: deps + '/@testing-library/react/dist/index.js'},
    {find: /^vitest$/, replacement: deps + '/vitest/dist/index.js'},
    {find: /^@tryghost\/admin-x-framework\/hooks$/, replacement: local('framework-stub.ts')},
    {find: /^@tryghost\/admin-x-framework\/api\/settings$/, replacement: local('settings-stub.ts')},
    {find: /^@tryghost\/shade\/utils$/, replacement: local('shade-stub.ts')},
    {find: '@/', replacement: local('apps/admin/src/') + '/'},
  ]},
  test: {
    environment: 'jsdom',
    include: ['apps/admin-x-framework/test/unit/hooks/use-form.test.ts', 'apps/admin/src/settings/hooks/use-setting-group.test.tsx'],
    globals: true,
    fileParallelism: false,
    maxWorkers: 1,
    reporters: ['verbose'],
  },
};
"""
status = 1
sandbox = None
try:
    with tempfile.TemporaryDirectory(prefix='.tmp-sandbox-settings-test-', dir=root) as name:
        sandbox = Path(name).resolve()
        if sandbox.parent != root or not sandbox.name.startswith('.tmp-sandbox-settings-test-'):
            raise RuntimeError(f'Unsafe sandbox path: {sandbox}')
        print('SANDBOX', sandbox, flush=True)
        for item in files:
            target = sandbox / item
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / item, target)
        (sandbox / 'framework-stub.ts').write_text("export {default as useForm} from './apps/admin-x-framework/src/hooks/use-form';\nexport const useHandleError = () => () => {};\n", encoding='utf-8')
        (sandbox / 'settings-stub.ts').write_text("export const useEditSettings = () => { throw new Error('Unmocked settings mutation'); };\n", encoding='utf-8')
        (sandbox / 'shade-stub.ts').write_text("export const useGlobalDirtyState = () => { throw new Error('Unmocked dirty state'); };\n", encoding='utf-8')
        (sandbox / 'vitest.config.mjs').write_text(config, encoding='utf-8')
        env = os.environ.copy()
        for key in ('TEMP', 'TMP', 'TMPDIR', 'XDG_CACHE_HOME'):
            env[key] = str(sandbox)
        env.update(NODE_OPTIONS='--max-old-space-size=4096', NX_DAEMON='false', CI='1', UV_THREADPOOL_SIZE='1')
        command = [str(node), str(deps / 'vitest/vitest.mjs'), 'run', '--config', str(sandbox / 'vitest.config.mjs'), '--pool=threads', '--maxWorkers=1', '--no-file-parallelism'] + sys.argv[1:]
        subprocess.run([str(node), '--version'], cwd=sandbox, env=env, check=True)
        print('COMMAND', ' '.join(command), flush=True)
        result = subprocess.run(command, cwd=sandbox, env=env, timeout=90)
        status = result.returncode
        print('VITEST_EXIT_CODE', status, flush=True)
finally:
    if sandbox is not None:
        print('SANDBOX_CLEANUP', not sandbox.exists(), flush=True)
sys.exit(status)
~~~