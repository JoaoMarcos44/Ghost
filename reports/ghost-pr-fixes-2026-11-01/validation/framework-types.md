# Integrated framework type check

The official `@tryghost/admin-x-framework` type check passed with the three fixes
combined with main. No type errors were reported, including in files changed by
the fixes.

## Inputs

- Main: `3b395b6b082bb995bc8dc8d7b648fea7732fe839`
- Toggle: `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`
- Settings: `1958aa6821284e1caba9c6cf88c222753d6aacf8`
- Member labels: `1cdac3b534035e02d995160c0b37d330e47b5ea5`
- Previously assembled integration tree: `b9e69e2a3fb484830f4c869dba287e9b56567408`

The runner checked the inputs against `integrated-results.json` and archived
that integration tree into a disposable sandbox. It linked installed
dependencies from the settings worktree, with workspace links targeting the
sandbox copy, and copied the previously generated Shade declarations. The
Shade source had no changes between the integrated tree and the settings
commit; its settings worktree was clean under `apps/shade`.

## Commands and results

From the repository root, the runner was invoked as:

```powershell
python reports/ghost-pr-fixes-2026-11-01/validation/framework-types.py
```

It used the native pnpm 12.16.1 executable from
`C:\Users\Nitro\AppData\Local\pnpm\.tools\pnpm\12.16.1_tmp_22488_0\node_modules\@pnpm\exe.win32-x64\pnpm.exe`
to execute the following official package scripts from the sandbox, in order:

```text
pnpm --dir packages/app-contracts build          exit 0
pnpm --dir packages/nql-string build             exit 0
pnpm --dir packages/metafield-types build         exit 0
pnpm --dir packages/metafield-csv build           exit 0
pnpm --dir packages/checkout build                exit 0
pnpm --dir packages/adapters/upgrade-base build   exit 0
pnpm --dir packages/limit-service build           exit 0
pnpm --dir apps/admin-x-framework test:types      exit 0
```

Each build runs its package's `tsc` script and produced the expected real
`build/index.d.ts`; `metafield-types` was built before its dependent packages.
The framework's `test:types` script runs `tsc --noEmit`. The runner exited 0.

Commands ran offline, with a 2048 MB Node heap limit, concurrency set to one,
and a 180-second timeout and Windows Job process-tree cleanup per command. The
sandbox `.tmp-sandbox-validation-types-61exyg0h` was removed after the run.

## Limits

The check reused installed dependencies instead of bootstrapping or installing
the integrated lockfile. The installed TypeScript 6.0.2 and Zod 4.6.7 match the
main catalog, but the settings worktree lockfile differs from main. Thus this
result does not establish that a fresh installation of the integrated lockfile
would produce identical dependency resolution.

The runner depends on the existing `integrated-results.json` record and the
previously generated Shade declarations at
`.tmp-sandbox-validation-shade-c78fb073ce/source/apps/shade/types`; those
declarations must be rebuilt if that temporary directory is removed.
