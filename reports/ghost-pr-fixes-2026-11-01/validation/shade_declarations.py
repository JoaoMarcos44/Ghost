"""Build real Shade declarations in an isolated sandbox for temporary hooks."""

from pathlib import Path
import os
import runpy
import shutil
import subprocess
import sys
import uuid


ROOT = Path(r"C:\Users\Nitro\Ghost").resolve()
SOURCE = ROOT / ".worktrees" / "fix-settings-pending-save-20261031"
NODE = SOURCE / "node_modules" / ".bin" / "node.exe"
PNPM = Path(r"C:\Users\Nitro\AppData\Roaming\npm\node_modules\pnpm\bin\pnpm.cjs")
HELPER = runpy.run_path(str(Path(r"C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31\validation\run_checks.py")), run_name="validation_helpers")


def main():
    sandbox = ROOT / (".tmp-sandbox-validation-shade-" + uuid.uuid4().hex[:10])
    sandbox.mkdir()
    keep = False
    try:
        repo = sandbox / "source"
        shade = repo / "apps" / "shade"
        paths = subprocess.check_output(
            ["git", "ls-files", "-z", "--", "apps/shade", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", ".pnpmfile.mjs"],
            cwd=SOURCE,
        )
        count = 0
        for raw in paths.split(b"\0"):
            if not raw:
                continue
            relative = raw.decode("utf-8")
            if HELPER["excluded"](relative):
                continue
            origin, destination = SOURCE / relative, repo / relative
            if origin.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin, destination)
                count += 1
        if not NODE.is_file() or not PNPM.is_file() or count == 0:
            raise RuntimeError("Missing installed runtime, pnpm, or tracked Shade source")

        subprocess.run(
            [str(NODE), "-e", "require('node:fs').symlinkSync(process.argv[1],process.argv[2],'junction')",
             str(SOURCE / "apps" / "shade" / "node_modules"), str(shade / "node_modules")],
            check=True,
        )
        empty_config = sandbox / "empty.npmrc"
        empty_config.write_text("", encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "NODE_OPTIONS": "--max-old-space-size=2048", "NX_DAEMON": "false", "NX_PARALLEL": "1",
            "VITEST_MAX_WORKERS": "1", "RAYON_NUM_THREADS": "1", "CI": "true",
            "pnpm_config_verify_deps_before_run": "false", "pnpm_config_offline": "true",
            "npm_config_offline": "true", "COREPACK_ENABLE_NETWORK": "0",
            "npm_config_userconfig": str(empty_config), "npm_config_globalconfig": str(empty_config),
            "npm_config_cache": str(sandbox / "npm-cache"), "XDG_CACHE_HOME": str(sandbox / "cache"),
            "TEMP": str(sandbox), "TMP": str(sandbox), "TMPDIR": str(sandbox),
            "NO_COLOR": "1", "FORCE_COLOR": "0", "PATH": str(NODE.parent) + os.pathsep + env["PATH"],
        })
        run = HELPER["run"]
        commands = [
            ("pnpm exec tsc -p tsconfig.declaration.json", [str(NODE), str(PNPM), "exec", "tsc", "-p", "tsconfig.declaration.json"]),
            ("pnpm exec tsc-alias -p tsconfig.declaration.json", [str(NODE), str(PNPM), "exec", "tsc-alias", "-p", "tsconfig.declaration.json"]),
            ("node scripts/check-declarations.ts", [str(NODE), "scripts/check-declarations.ts"]),
        ]
        for label, command in commands:
            code = run(label, command, shade, env)
            if code:
                return code

        declarations = shade / "types"
        exported = declarations / "utils.d.ts"
        implementation = declarations / "hooks" / "use-global-dirty-state.d.ts"
        if not implementation.is_file() or "useGlobalDirtyState" not in exported.read_text(encoding="utf-8"):
            raise RuntimeError("Expected Shade hook declaration or export missing")
        keep = True
        print(f"SHADE_TYPES={declarations}", flush=True)
        print("Sandbox retained for the parent hooks; remove worktree junctions before cleanup.", flush=True)
        return 0
    finally:
        if not keep:
            HELPER["remove_sandbox"](sandbox)


if __name__ == "__main__":
    sys.exit(main())
