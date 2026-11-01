"""Check integrated framework types with real workspace declaration builds."""

from pathlib import Path
import json
import os
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(r'C:\Users\Nitro\Ghost').resolve()
SOURCE = ROOT / '.worktrees/fix-settings-pending-save-20261031'
REPORT = ROOT / 'reports/ghost-pr-fixes-2026-11-01/validation'
H = runpy.run_path(str(ROOT / 'reports/ghost-prs-2026-10-31/validation/run_checks.py'), run_name='helpers')
NODE = SOURCE / 'node_modules/.bin/node.exe'
PNPM = Path(r'C:\Users\Nitro\AppData\Local\pnpm\.tools\pnpm\12.16.1_tmp_22488_0\node_modules\@pnpm\exe.win32-x64\pnpm.exe')
SHADE = ROOT / '.tmp-sandbox-validation-shade-c78fb073ce/source/apps/shade/types'
MAIN = '3b395b6b082bb995bc8dc8d7b648fea7732fe839'
HEADS = {
    'fix/toggle-html-roundtrip-20261031': '4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef',
    'fix/settings-pending-save-20261031': '1958aa6821284e1caba9c6cf88c222753d6aacf8',
    'fix/member-label-removal-20261031': '1cdac3b534035e02d995160c0b37d330e47b5ea5',
}
BUILD_PATHS = [
    'packages/app-contracts',
    'packages/nql-string',
    'packages/metafield-types',
    'packages/metafield-csv',
    'packages/checkout',
    'packages/adapters/upgrade-base',
    'packages/limit-service',
]


def main():
    previous = json.loads((REPORT / 'integrated-results.json').read_text(encoding='utf-8'))
    if previous['main'] != MAIN or previous['heads'] != HEADS:
        raise RuntimeError('Integration record does not match the requested commits')
    tree = previous['integration_tree']
    scratch = Path(tempfile.mkdtemp(prefix='.tmp-sandbox-validation-types-', dir=ROOT))
    try:
        repo = scratch / 'repo'
        repo.mkdir()
        archive = scratch / 'source.tar'
        subprocess.run(['git', 'archive', '--format=tar', '--output', str(archive), tree],
                       cwd=ROOT, check=True, timeout=180)
        with tarfile.open(archive) as tar:
            members = [m for m in tar if m.isfile() and not H['excluded'](m.name)]
            tracked = [m.name for m in members]
            tar.extractall(repo, members=members, filter='data')

        empty = scratch / 'empty.npmrc'
        empty.write_text('', encoding='utf-8')
        env = os.environ.copy()
        env.update(
            NODE_OPTIONS='--max-old-space-size=2048', NX_DAEMON='false', NX_PARALLEL='1',
            NX_NATIVE_COMMAND_RUNNER='false', NX_NO_CLOUD='true', NX_SKIP_NX_CACHE='true',
            NX_SKIP_REMOTE_CACHE='true', VITEST_MAX_WORKERS='1', RAYON_NUM_THREADS='1',
            CI='true', pnpm_config_verify_deps_before_run='false', pnpm_config_offline='true',
            npm_config_offline='true', COREPACK_ENABLE_NETWORK='0',
            npm_config_userconfig=str(empty), npm_config_globalconfig=str(empty),
            npm_config_cache=str(scratch / 'npm-cache'), XDG_CACHE_HOME=str(scratch / 'cache'),
            TEMP=str(scratch), TMP=str(scratch), TMPDIR=str(scratch),
            NX_CACHE_DIRECTORY=str(scratch / 'nx-cache'), NX_WORKSPACE_DATA_DIRECTORY=str(scratch / 'nx-data'),
            GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='NUL', GIT_TERMINAL_PROMPT='0',
            NO_COLOR='1', FORCE_COLOR='0',
            PATH=os.pathsep.join((str(NODE.parent), str(PNPM.parent), env['PATH'])),
        )
        H['dependency_links'](SOURCE, repo, tracked, NODE)
        shutil.copytree(SHADE, repo / 'apps/shade/types')
        print(f'Integration tree: {tree}', flush=True)
        for package in BUILD_PATHS:
            command = [str(PNPM), '--dir', package, 'build']
            if H['run'](' '.join(command), command, repo, env):
                return 1
            declaration = repo / package / 'build/index.d.ts'
            if not declaration.is_file():
                raise RuntimeError(f'Missing expected generated declaration: {package}/build/index.d.ts')

        command = [str(PNPM), '--dir', 'apps/admin-x-framework', 'test:types']
        return H['run'](' '.join(command), command, repo, env)
    finally:
        H['remove_sandbox'](scratch)


if __name__ == '__main__':
    sys.exit(main())
