"""Run a Ghost check in a disposable, source-only Windows sandbox.

Usage: python run_checks.py {settings,member,toggle} [--types]
Only run after the orchestrator has granted a test slot.
"""

import argparse
from collections import deque
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import uuid


ROOT = Path(r"C:\Users\Nitro\Ghost").resolve()
WORKTREES = {
    "settings": "fix-settings-pending-save-20261031",
    "member": "fix-member-label-removal-20261031",
    "toggle": "fix-toggle-html-roundtrip-20261031",
}
EXTRA = {
    "settings": ["apps/admin/src/settings/hooks/use-setting-group.test.tsx"],
    "member": [],
    "toggle": [".changeset/restore-toggle-html.md"],
}
TYPES = {
    "settings": ["@tryghost/admin-x-framework", "@tryghost/admin"],
    "member": ["@tryghost/admin-x-framework", "@tryghost/admin", "ghost"],
    "toggle": ["@tryghost/kg-default-nodes", "@tryghost/kg-html-to-lexical"],
}


def checked(command, cwd, env=None):
    return subprocess.check_output(command, cwd=cwd, env=env)


def entries(source):
    output = checked(["git", "ls-files", "--stage", "-z"], source)
    for record in output.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, obj, stage = meta.decode("ascii").split()
        if stage != "0":
            raise RuntimeError("Unmerged index entry; refusing to copy")
        yield mode, obj, raw_path.decode("utf-8")


def excluded(relative):
    # Local settings and credentials never enter the sandbox, even if tracked.
    name = Path(relative).name.lower()
    return (
        name in {".npmrc", ".pnpmrc", ".env"}
        or (name.startswith(".env.") and not name.endswith(".example"))
        or "config.local" in name
        or Path(name).suffix in {".pem", ".key", ".p12", ".pfx", ".jks"}
    )


def copy_tracked(source, target, source_prefix=Path()):
    tracked = []
    submodules = []
    eligible = {}
    for mode, obj, relative in entries(source):
        if excluded(relative):
            continue
        local = Path(relative)
        origin = source / local
        if mode == "160000":
            submodules.append((obj, source_prefix / local))
            if origin.is_dir():
                copy_tracked(origin, target, source_prefix / local)
            continue
        if not origin.is_file() and not (mode == "120000" and origin.is_symlink()):
            continue  # Includes tracked files deleted in the working tree.
        eligible[relative] = mode
        tracked.append((source_prefix / local).as_posix())

    archive_path = target.parent / f"source-{uuid.uuid4().hex}.tar"
    with archive_path.open("wb") as output:
        subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=source, stdout=output, check=True, timeout=120)
    selected = set()

    def regular_members(archive):
        for member in archive:
            if member.isfile() and member.name in eligible:
                selected.add(member.name)
                yield member

    destination_root = target / source_prefix
    destination_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination_root, members=regular_members(archive), filter="data")

    changed = checked(["git", "diff", "--name-only", "-z", "HEAD"], source)
    overlay = set(eligible) - selected
    overlay.update(p.decode("utf-8") for p in changed.split(b"\0") if p)
    for relative in overlay:
        if relative not in eligible:
            continue
        origin = source / relative
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if eligible[relative] == "120000" and origin.is_symlink():
            destination.write_text(os.readlink(origin), encoding="utf-8")
        elif origin.is_file():
            shutil.copyfile(origin, destination)
    return tracked, submodules


def make_index(source, repo, tracked, submodules, scratch, env):
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True, env=env)
    pathspec = scratch / "tracked-paths.bin"
    pathspec.write_bytes(b"\0".join(p.encode("utf-8") for p in tracked) + b"\0")
    subprocess.run(
        ["git", "--literal-pathspecs", "add", "-f", "--pathspec-from-file=" + str(pathspec), "--pathspec-file-nul"],
        cwd=repo,
        env=env,
        check=True,
    )
    for obj, path in submodules:
        subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo", f"160000,{obj},{path.as_posix()}"],
            cwd=repo,
            env=env,
            check=True,
        )


def copy_bin(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.is_file() and item.name.lower() != "node.exe":
            shutil.copyfile(item, destination / item.name)


def dependency_links(source, repo, tracked, node):
    package_dirs = {Path()}
    package_dirs.update(Path(p).parent for p in tracked if Path(p).name == "package.json")
    links = []

    def add_dependency(item, destination):
        if not item.is_dir():
            return
        actual = item.resolve(strict=True)
        try:
            local = actual.relative_to(source)
        except ValueError:
            target = item  # Read through the installed external dependency.
        else:
            target = item if "node_modules" in local.parts else repo / local
        if not target.is_dir():
            raise RuntimeError(f"Workspace dependency not copied into sandbox: {local}")
        links.append([str(destination), str(target)])

    for package in sorted(package_dirs, key=str):
        installed = source / package / "node_modules"
        if not installed.is_dir():
            continue
        destination = repo / package / "node_modules"
        destination.mkdir(parents=True, exist_ok=True)
        for item in installed.iterdir():
            if item.name == ".bin" and item.is_dir():
                copy_bin(item, destination / item.name)
            elif item.name.startswith("."):
                continue  # No installed caches or machine-specific state.
            elif item.name.startswith("@") and item.is_dir():
                scope = destination / item.name
                scope.mkdir(exist_ok=True)
                for scoped in item.iterdir():
                    add_dependency(scoped, scope / scoped.name)
            else:
                add_dependency(item, destination / item.name)

    # Node creates Windows junctions without developer-mode symlink privileges.
    program = "const fs=require('fs');for(const [d,s] of JSON.parse(fs.readFileSync(0,'utf8')))fs.symlinkSync(s,d,'junction')"
    subprocess.run([str(node), "-e", program], input=json.dumps(links), text=True, check=True)
    print(f"Linked {len(links)} dependencies; workspace links target sandbox copies.", flush=True)


class Job:
    """Terminate the command's Windows process tree on exit or interruption."""

    def __init__(self):
        class Basic(ctypes.Structure):
            _fields_ = [("p", ctypes.c_int64), ("j", ctypes.c_int64), ("flags", wintypes.DWORD),
                        ("min", ctypes.c_size_t), ("max", ctypes.c_size_t), ("active", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]

        class Io(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("r", "w", "o", "rb", "wb", "ob")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", Io), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process):
        if not self.kernel.AssignProcessToJobObject(self.handle, wintypes.HANDLE(process._handle)):
            process.terminate()
            process.wait()
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        self.kernel.CloseHandle(self.handle)


def run(label, command, cwd, env):
    print("\nRUN", label, flush=True)
    job = Job()
    process = None
    timed_out = threading.Event()
    timer = None
    try:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        job.assign(process)
        def terminate_on_timeout():
            timed_out.set()
            job.kernel.TerminateJobObject(job.handle, 124)

        timer = threading.Timer(180, terminate_on_timeout)
        timer.start()
        tail = deque(process.stdout, maxlen=160)
        code = process.wait()
        if timed_out.is_set():
            code = 124
            print(f"TIMEOUT {label}: 180 seconds", flush=True)
        if code:
            print("".join(tail), end="", flush=True)
        print(f"RESULT {label}: exit {code}", flush=True)
        return code
    finally:
        if timer is not None:
            timer.cancel()
        job.close()
        if process is not None and process.poll() is None:
            process.wait(timeout=10)


def remove_sandbox(scratch):
    resolved = scratch.resolve(strict=True)
    if resolved.parent != ROOT or not resolved.name.startswith(".tmp-sandbox-validation-") or scratch.is_symlink() or scratch.is_junction():
        raise RuntimeError(f"Refusing cleanup of unexpected sandbox path: {resolved}")

    # Remove junction entries themselves before walking or deleting their targets.
    for current, directories, _ in os.walk(resolved, topdown=True, followlinks=False):
        parent = Path(current).resolve(strict=True)
        if not parent.is_relative_to(resolved):
            raise RuntimeError(f"Refusing to traverse outside sandbox: {parent}")
        for name in directories[:]:
            entry = parent / name
            if entry.is_junction() or entry.is_symlink():
                entry.rmdir()
                directories.remove(name)

    def clear_readonly_and_retry(function, path, error):
        item = Path(path)
        if (not isinstance(error, PermissionError) or function is not os.unlink
                or item.is_symlink() or item.is_junction() or not item.is_file()
                or not item.resolve(strict=True).is_relative_to(resolved)):
            raise error
        os.chmod(item, item.stat().st_mode | stat.S_IWRITE)
        function(path)

    shutil.rmtree(resolved, onexc=clear_readonly_and_retry)
    print(f"Sandbox removed: {resolved.name}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("worktree", choices=WORKTREES)
    parser.add_argument("--types", action="store_true")
    args = parser.parse_args()
    source = (ROOT / ".worktrees" / WORKTREES[args.worktree]).resolve(strict=True)
    if source.parent != (ROOT / ".worktrees").resolve():
        raise RuntimeError("Unexpected source path")
    node = source / "node_modules" / ".bin" / "node.exe"
    pnpm_cmd = Path(shutil.which("pnpm.cmd") or "")
    pnpm = pnpm_cmd.parent / "node_modules" / "pnpm" / "bin" / "pnpm.cjs"
    if not node.is_file() or not pnpm.is_file():
        raise RuntimeError("Installed Node 22 or pnpm CLI not found")

    scratch = ROOT / (".tmp-sandbox-validation-" + uuid.uuid4().hex[:10])
    scratch.mkdir()
    try:
        repo = scratch / "repo"
        repo.mkdir()
        env = os.environ.copy()
        empty_config = scratch / "empty.npmrc"
        empty_config.write_text("", encoding="utf-8")
        env.update({
            "NODE_OPTIONS": "--max-old-space-size=4096", "NX_DAEMON": "false", "NX_PARALLEL": "1",
            "NX_NO_CLOUD": "true", "NX_SKIP_NX_CACHE": "true", "NX_SKIP_REMOTE_CACHE": "true",
            "VITEST_MAX_WORKERS": "1", "CI": "true", "pnpm_config_verify_deps_before_run": "false",
            "npm_config_offline": "true", "pnpm_config_offline": "true", "COREPACK_ENABLE_NETWORK": "0",
            "npm_config_userconfig": str(empty_config), "npm_config_globalconfig": str(empty_config),
            "npm_config_cache": str(scratch / "npm-cache"), "XDG_CACHE_HOME": str(scratch / "cache"),
            "NX_CACHE_DIRECTORY": str(scratch / "nx-cache"), "NX_WORKSPACE_DATA_DIRECTORY": str(scratch / "nx-data"),
            "TEMP": str(scratch), "TMP": str(scratch), "TMPDIR": str(scratch), "NO_COLOR": "1",
            "FORCE_COLOR": "0", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "NUL", "GIT_TERMINAL_PROMPT": "0",
            "PATH": os.pathsep.join([str(repo / "node_modules" / ".bin"), str(node.parent), env["PATH"]]),
        })
        tracked, submodules = copy_tracked(source, repo)
        for relative in EXTRA[args.worktree]:
            original, destination = source / relative, repo / relative
            if original.is_file() and relative not in tracked:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
                tracked.append(relative)
        make_index(source, repo, tracked, submodules, scratch, env)
        dependency_links(source, repo, tracked, node)

        changed = checked(["git", "diff", "--name-only", "--diff-filter=ACMRT", "-z", "HEAD"], source)
        changed_paths = [p.decode("utf-8") for p in changed.split(b"\0") if p]
        changed_paths += [p for p in EXTRA[args.worktree] if (repo / p).is_file()]
        format_paths = sorted({p for p in changed_paths if Path(p).suffix in {".css", ".js", ".jsx", ".json", ".jsonc", ".md", ".mjs", ".ts", ".tsx"} and (repo / p).is_file()})
        cli = [str(node), str(pnpm)]
        check_code = run("pnpm check", cli + ["check"], repo, env)
        format_code = 0
        if check_code and format_paths:
            format_code = run("pnpm exec oxfmt --check changed files", cli + ["exec", "oxfmt", "--check"] + format_paths, repo, env)
        types_code = 0
        if args.types and not format_code:
            for project in TYPES[args.worktree]:
                types_code = run(f"pnpm nx run {project}:test:types", cli + ["nx", "run", f"{project}:test:types"], repo, env)
                if types_code:
                    break
        return 1 if check_code or format_code or types_code else 0
    finally:
        remove_sandbox(scratch)


if __name__ == "__main__":
    sys.exit(main())
