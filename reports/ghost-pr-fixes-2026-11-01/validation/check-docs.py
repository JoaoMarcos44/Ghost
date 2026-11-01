"""Format and validate the published evidence in a disposable sandbox."""
from pathlib import Path
import ast, json, os, re, runpy, shutil, tempfile

root = Path(r'C:\Users\Nitro\Ghost')
report = root/'reports/ghost-pr-fixes-2026-11-01'
source = root/'.worktrees/fix-settings-pending-save-20261031'
node = source/'node_modules/.bin/node.exe'
helper = runpy.run_path(str(root/'reports/ghost-prs-2026-10-31/validation/run_checks.py'), run_name='helpers')
scratch = Path(tempfile.mkdtemp(prefix='.tmp-sandbox-validation-docs-', dir=root))
paths = sorted(p for p in report.rglob('*') if p.suffix in ('.md','.json','.py','.ps1') and 'commit' not in p.name)
try:
    for config in ('.oxfmtrc.json','.editorconfig','.markdownlint-cli2.jsonc'):
        shutil.copyfile(root/config, scratch/config)
    for path in paths:
        destination = scratch/path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    env = os.environ.copy()
    env.update(TEMP=str(scratch), TMP=str(scratch), TMPDIR=str(scratch), XDG_CACHE_HOME=str(scratch/'cache'), NODE_OPTIONS='--max-old-space-size=2048')
    formatted = [str(p.relative_to(root)) for p in paths if p.suffix in ('.md','.json')]
    for label, command in [
        ('format evidence',[str(node),str(source/'node_modules/oxfmt/bin/oxfmt'),'--threads=1',*formatted]),
        ('check evidence formatting',[str(node),str(source/'node_modules/oxfmt/bin/oxfmt'),'--check','--threads=1',*formatted]),
        ('markdownlint evidence',[str(node),str(source/'node_modules/markdownlint-cli2/markdownlint-cli2.mjs'),*filter(lambda p:p.endswith('.md'),formatted)]),
    ]:
        if helper['run'](label,command,scratch,env):
            raise RuntimeError(label+' failed')
    count = 0
    for path in paths:
        text = (scratch/path.relative_to(root)).read_text(encoding='utf-8')
        if path.suffix == '.py':
            ast.parse(text,filename=str(path))
        elif path.suffix == '.json':
            json.loads(text)
        elif path.suffix == '.md':
            if '\ufffd' in text or 'Corre??' in text:
                raise RuntimeError('Bad text encoding: '+str(path))
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if re.match(r'(?:https?://|#)',target):
                    continue
                target = target.split('#')[0]
                if target and not (path.parent/target).exists():
                    raise RuntimeError('Missing local link: '+target+' in '+str(path))
                count += 1
    for path in paths:
        if path.suffix in ('.md','.json'):
            shutil.copyfile(scratch/path.relative_to(root),path)
    print(json.dumps({'artifacts':len(paths),'local_links':count,'result':'passed'}),flush=True)
finally:
    helper['remove_sandbox'](scratch)
