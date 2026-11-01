"""Check the three fixed source branches combined with the inspected upstream main."""
from pathlib import Path
import json, os, runpy, shutil, subprocess, sys, tarfile, tempfile

ROOT = Path(r'C:\Users\Nitro\Ghost')
SOURCE = ROOT / '.worktrees/fix-settings-pending-save-20261031'
REPORT = ROOT / 'reports/ghost-pr-fixes-2026-11-01/validation'
H = runpy.run_path(str(ROOT / 'reports/ghost-prs-2026-10-31/validation/run_checks.py'), run_name='helpers')
MAIN = '3b395b6b082bb995bc8dc8d7b648fea7732fe839'
BRANCHES = ['fix/toggle-html-roundtrip-20261031','fix/settings-pending-save-20261031','fix/member-label-removal-20261031']
NODE = SOURCE / 'node_modules/.bin/node.exe'
PNPM = Path(r'C:\Users\Nitro\AppData\Local\pnpm\.tools\pnpm\12.16.1_tmp_22488_0\node_modules\@pnpm\exe.win32-x64\pnpm.exe')
SHADE = ROOT / '.tmp-sandbox-validation-shade-c78fb073ce/source/apps/shade/types'
env = os.environ.copy()
name,email = subprocess.check_output(['git','show','-s','--format=%an%n%ae','HEAD'],cwd=SOURCE,text=True).strip().splitlines()
env.update(GIT_AUTHOR_NAME=name,GIT_AUTHOR_EMAIL=email,GIT_COMMITTER_NAME=name,GIT_COMMITTER_EMAIL=email)
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,env=env,text=True).strip()
integrated=MAIN
heads={}
for branch in BRANCHES:
    head=git('rev-parse',branch)
    heads[branch]=head
    tree=git('merge-tree','--write-tree',integrated,head).splitlines()[0]
    integrated=git('commit-tree',tree,'-p',integrated,'-p',head,'-m','Temporary validation merge; no branch updated')
scratch=Path(tempfile.mkdtemp(prefix='.tmp-sandbox-validation-integrated-',dir=ROOT))
results={'main':MAIN,'heads':heads,'integration_tree':git('rev-parse',integrated+'^{tree}'),
         'dependency_note':'Reused installed dependency versions from the source worktree; no new install of main lockfile.'}
prior = REPORT/'integrated-results.json'
if prior.is_file() and not (REPORT/'integrated-results-first.json').exists():
    shutil.copyfile(prior, REPORT/'integrated-results-first.json')
try:
    repo=scratch/'repo'
    repo.mkdir()
    archive=scratch/'source.tar'
    subprocess.run(['git','-c','core.autocrlf=false','archive','--format=tar','--output',str(archive),integrated],cwd=ROOT,check=True)
    with tarfile.open(archive) as tar:
        all_members = list(tar)
        members=[m for m in all_members if m.isfile() and not H['excluded'](m.name)]
        tracked=[m.name for m in members]
        tar.extractall(repo,members=members,filter='data')
        symlink_errors=[]
        for member in all_members:
            if not member.issym():
                continue
            destination=repo/member.name
            target=(destination.parent/member.linkname).resolve()
            if not target.is_relative_to(repo.resolve()):
                raise RuntimeError('Archive symlink escapes sandbox')
            destination.parent.mkdir(parents=True,exist_ok=True)
            try:
                destination.symlink_to(member.linkname,target_is_directory=target.is_dir())
            except OSError as error:
                symlink_errors.append({'path':member.name,'error':str(error)})
        results['symlink_errors']=symlink_errors
    env.update(NODE_OPTIONS='--max-old-space-size=2048',NX_DAEMON='false',NX_PARALLEL='1',NX_NATIVE_COMMAND_RUNNER='false',
        NX_NO_CLOUD='true',NX_SKIP_NX_CACHE='true',NX_SKIP_REMOTE_CACHE='true',VITEST_MAX_WORKERS='1',
        CI='true',pnpm_config_verify_deps_before_run='false',pnpm_config_offline='true',COREPACK_ENABLE_NETWORK='0',
        XDG_CACHE_HOME=str(scratch/'cache'),TEMP=str(scratch),TMP=str(scratch),TMPDIR=str(scratch),
        NX_CACHE_DIRECTORY=str(scratch/'nx-cache'),NX_WORKSPACE_DATA_DIRECTORY=str(scratch/'nx-data'),
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='NUL',GIT_TERMINAL_PROMPT='0',
        PATH=os.pathsep.join((str(NODE.parent),str(PNPM.parent),env['PATH'])))
    empty=scratch/'empty.npmrc'; empty.write_text('')
    env.update(npm_config_userconfig=str(empty),npm_config_globalconfig=str(empty),npm_config_cache=str(scratch/'npm-cache'))
    subprocess.run(['git','init','--quiet',str(repo)],env=env,check=True)
    alternates=repo/'.git/objects/info/alternates'
    alternates.write_bytes(((ROOT/'.git/objects').as_posix()+'\n').encode('utf-8'))
    subprocess.run(['git','read-tree',integrated],cwd=repo,env=env,check=True)
    H['dependency_links'](SOURCE,repo,tracked,NODE)
    shutil.copytree(SHADE,repo/'apps/shade/types')
    results['pnpm_check_exit']=H['run']('pnpm check on combined main tree',[str(PNPM),'check'],repo,env)
    results['framework_types_note']='Validated separately after real workspace declaration builds; see framework-types.md.'
    results['cleanup_pending']=False
finally:
    H['remove_sandbox'](scratch)
    (REPORT/'integrated-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results),flush=True)
sys.exit(0 if results.get('pnpm_check_exit')==0 else 1)

