param(
    [Parameter(Mandatory = $true)]
    [string]$Worktree
)

$ErrorActionPreference = 'Stop'
$head = '2a62cbb7447c2c52e6b2be4029803f6ee64002d9'
$base = '80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b'
$worktreePath = (Resolve-Path -LiteralPath $Worktree).Path
$actualHead = (& git -C $worktreePath rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualHead -ne $head) { throw 'Unexpected worktree HEAD' }
$sandboxParent = (Resolve-Path -LiteralPath (Join-Path $worktreePath 'apps/admin')).Path
$sandbox = Join-Path $sandboxParent ('.tmp-pr32433-probe-' + [guid]::NewGuid().ToString('N'))
$evidence = Split-Path -Parent $PSCommandPath
$result = 1
$pushed = $false

try {
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    foreach ($name in @('head', 'base')) {
        New-Item -ItemType Directory -Path (Join-Path $sandbox $name) | Out-Null
        $revision = if ($name -eq 'head') { $head } else { $base }
        foreach ($entry in @(
            @{ source = 'apps/admin-x-framework/src/hooks/use-form.ts'; target = 'use-form.ts' },
            @{ source = 'apps/admin/src/settings/hooks/use-setting-group.tsx'; target = 'use-setting-group.tsx' },
            @{ source = 'apps/admin/src/settings/site/design-and-branding/use-design-form.ts'; target = 'use-design-form.ts' }
        )) {
            $content = (& git -C $worktreePath show ($revision + ':' + $entry.source)) -join "`n"
            if ($LASTEXITCODE -ne 0) { throw "git show failed for $($entry.source) at $revision" }
            # Preserve the production hook bodies; replace imports only, so the
            # sandbox uses real local hooks and isolated API/context test doubles.
            $content = $content.Replace("'@tryghost/admin-x-framework/hooks'", "'./hooks-shim'")
            $content = $content.Replace("'@tryghost/admin-x-framework/api/settings'", "'../shared'")
            $content = $content.Replace("'@tryghost/admin-x-framework/api/custom-theme-settings'", "'../shared'")
            $content = $content.Replace("'@/settings/providers/global-data-context'", "'../shared'")
            $content = $content.Replace("'@tryghost/shade/utils'", "'../shared'")
            [IO.File]::WriteAllText((Join-Path (Join-Path $sandbox $name) $entry.target), $content + "`n")
        }
        [IO.File]::WriteAllText((Join-Path (Join-Path $sandbox $name) 'hooks-shim.ts'), @'
export { default as useForm } from './use-form';
export const useHandleError = () => () => {};
'@)
    }
    Copy-Item -LiteralPath (Join-Path $evidence 'probe-shared.tsx') -Destination (Join-Path $sandbox 'shared.tsx')
    Copy-Item -LiteralPath (Join-Path $evidence 'probe.test.tsx') -Destination (Join-Path $sandbox 'probe.test.tsx')
    Copy-Item -LiteralPath (Join-Path $evidence 'probe.vitest.config.mjs') -Destination (Join-Path $sandbox 'vitest.config.mjs')
    $env:NODE_OPTIONS = '--max-old-space-size=2048'
    $env:TEMP = $sandbox
    $env:TMP = $sandbox
    $env:XDG_CACHE_HOME = Join-Path $sandbox 'cache'
    Push-Location -LiteralPath $sandbox
    $pushed = $true
    # Invoke the installed pinned runtime without pnpm's environment bootstrap.
    $nodeRuntime = Join-Path $worktreePath 'node_modules/.bin/node.exe'
    $vitestEntry = Join-Path $worktreePath 'apps/admin/node_modules/vitest/vitest.mjs'
    & $nodeRuntime --version
    & $nodeRuntime $vitestEntry run --config vitest.config.mjs --pool=threads --maxWorkers=1 --no-file-parallelism
    $result = $LASTEXITCODE
} finally {
    if ($pushed) { Pop-Location }
    if (Test-Path -LiteralPath $sandbox) {
        $target = (Resolve-Path -LiteralPath $sandbox).Path
        $expectedPrefix = $sandboxParent.TrimEnd('\') + '\.tmp-pr32433-probe-'
        if (!$target.StartsWith($expectedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean unexpected sandbox path: $target"
        }
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
exit $result
