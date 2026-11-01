param([Parameter(Mandatory = $true)][string]$Worktree)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Worktree).Path
$parent = (Resolve-Path -LiteralPath (Join-Path $root 'apps/admin')).Path
$sandbox = Join-Path $parent ('.tmp-pr32433-check-' + [guid]::NewGuid().ToString('N'))
$files = @(
    'apps/admin-x-framework/src/hooks/use-form.ts',
    'apps/admin/src/settings/general/user-detail-modal.tsx',
    'apps/admin/src/settings/general/user-detail-modal.test.tsx',
    'apps/admin/src/settings/hooks/use-save-button.ts',
    'apps/admin/src/settings/hooks/use-save-button.test.ts',
    'apps/admin/src/settings/hooks/use-setting-group.tsx',
    'apps/admin/src/settings/hooks/use-setting-group.test.tsx',
    'apps/admin/src/settings/membership/portal/portal-modal.tsx',
    'apps/admin/src/settings/membership/portal/portal-modal.test.tsx',
    'apps/admin/src/settings/membership/stripe/stripe-connect-modal.tsx',
    'apps/admin/src/settings/membership/stripe/stripe-connect-modal.test.tsx',
    'apps/admin/src/settings/site/design-and-branding/use-design-form.ts',
    'apps/admin/src/settings/site/design-and-branding/use-design-form.test.tsx',
    'apps/admin/src/settings/site/navigation-modal.tsx',
    'apps/admin/src/settings/site/navigation-modal.test.tsx'
)
$result = 1
$pushed = $false
try {
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    foreach ($file in $files) {
        $target = Join-Path $sandbox $file
        New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $root $file) -Destination $target
    }
    Copy-Item -LiteralPath (Join-Path $root '.oxfmtrc.json') -Destination $sandbox
    Copy-Item -LiteralPath (Join-Path $root '.oxlintrc.json') -Destination $sandbox
    Copy-Item -LiteralPath (Join-Path $root '.dependency-cruiser.cjs') -Destination $sandbox
    New-Item -ItemType Directory -Path (Join-Path $sandbox 'tools/configs') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'tools/configs/oxlint') -Destination (Join-Path $sandbox 'tools/configs/oxlint') -Recurse
    New-Item -ItemType Directory -Path (Join-Path $sandbox 'tools/scripts/ci') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'tools/scripts/ci/service-dependency-resolver.mjs') -Destination (Join-Path $sandbox 'tools/scripts/ci')
    New-Item -ItemType Directory -Path (Join-Path $sandbox 'ghost/core/server/services') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'ghost/core/server/services/service-inventory.yaml') -Destination (Join-Path $sandbox 'ghost/core/server/services')
    $env:NODE_OPTIONS = '--max-old-space-size=2048'
    $env:TEMP = $sandbox
    $env:TMP = $sandbox
    $env:XDG_CACHE_HOME = Join-Path $sandbox 'cache'
    Push-Location -LiteralPath $sandbox
    $pushed = $true
    $node = Join-Path $root 'node_modules/.bin/node.exe'
    & $node (Join-Path $root 'node_modules/oxfmt/bin/oxfmt') --check --threads=1 @files
    $formatResult = $LASTEXITCODE
    & $node (Join-Path $root 'node_modules/oxlint/bin/oxlint') --config .oxlintrc.json --deny-warnings --threads=1 @files
    $lintResult = $LASTEXITCODE
    if ($formatResult -eq 0 -and $lintResult -eq 0) { $result = 0 }
} finally {
    if ($pushed) { Pop-Location }
    if (Test-Path -LiteralPath $sandbox) {
        $target = (Resolve-Path -LiteralPath $sandbox).Path
        $prefix = $parent.TrimEnd('\') + '\.tmp-pr32433-check-'
        if (!$target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Unexpected sandbox path: $target" }
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
exit $result
