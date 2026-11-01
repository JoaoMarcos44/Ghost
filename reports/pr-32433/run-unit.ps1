param([Parameter(Mandatory = $true)][string]$Worktree, [string]$Filter = '', [string]$TestFile = '')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Worktree).Path
$parent = (Resolve-Path -LiteralPath (Join-Path $root 'apps/admin')).Path
$sandbox = Join-Path $parent ('.tmp-pr32433-fix-' + [guid]::NewGuid().ToString('N'))
$pushed = $false
$result = 1
try {
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    $files = @(
        @{ source = 'apps/admin-x-framework/src/hooks/use-form.ts'; target = 'use-form.ts' },
        @{ source = 'apps/admin-x-framework/test/unit/hooks/use-form.test.ts'; target = 'use-form.test.ts' },
        @{ source = 'apps/admin/src/settings/hooks/use-setting-group.tsx'; target = 'use-setting-group.tsx' },
        @{ source = 'apps/admin/src/settings/hooks/use-setting-group.test.tsx'; target = 'use-setting-group.test.tsx' },
        @{ source = 'apps/admin/src/settings/hooks/use-save-button.ts'; target = 'use-save-button.ts' },
        @{ source = 'apps/admin/src/settings/hooks/use-save-button.test.ts'; target = 'use-save-button.test.ts' },
        @{ source = 'apps/admin/src/settings/site/design-and-branding/use-design-form.ts'; target = 'use-design-form.ts' },
        @{ source = 'apps/admin/src/settings/site/design-and-branding/use-design-form.test.tsx'; target = 'use-design-form.test.tsx' },
        @{ source = 'apps/admin/src/settings/site/navigation-modal.tsx'; target = 'navigation-modal.tsx' },
        @{ source = 'apps/admin/src/settings/site/navigation-modal.test.tsx'; target = 'navigation-modal.test.tsx' },
        @{ source = 'apps/admin/src/settings/membership/stripe/stripe-connect-modal.tsx'; target = 'stripe-connect-modal.tsx' },
        @{ source = 'apps/admin/src/settings/membership/stripe/stripe-connect-modal.test.tsx'; target = 'stripe-connect-modal.test.tsx' },
        @{ source = 'apps/admin/src/settings/membership/portal/portal-modal.tsx'; target = 'portal-modal.tsx' },
        @{ source = 'apps/admin/src/settings/membership/portal/portal-modal.test.tsx'; target = 'portal-modal.test.tsx' },
        @{ source = 'apps/admin/src/settings/general/user-detail-modal.tsx'; target = 'user-detail-modal.tsx' },
        @{ source = 'apps/admin/src/settings/general/user-detail-modal.test.tsx'; target = 'user-detail-modal.test.tsx' },
        @{ source = 'apps/admin/src/settings/providers/global-data-context.ts'; target = 'context.ts' }
    )
    foreach ($file in $files) {
        $content = [IO.File]::ReadAllText((Join-Path $root $file.source))
        $content = $content.Replace("'../../../src/hooks/use-form'", "'./use-form'")
        $content = $content.Replace("'@tryghost/admin-x-framework/hooks'", "'./hooks-shim'")
        $content = $content.Replace("'@tryghost/admin-x-framework/api/settings'", "'./settings-shim'")
        $content = $content.Replace("'@tryghost/admin-x-framework/api/custom-theme-settings'", "'./theme-shim'")
        $content = $content.Replace("'@/settings/providers/global-data-context'", "'./context'")
        $content = $content.Replace("'@tryghost/shade/utils'", "'./shade-shim'")
        $content = $content.Replace("'@/settings/site/navigation/navigation-edit-form'", "'./navigation/navigation-edit-form'")
        $content = $content.Replace("'@/settings/general/users/profile-tab'", "'./users/profile-tab'")
        $content = $content.Replace("'@/settings/general/users/social-links-tab'", "'./users/social-links-tab'")
        $content = $content.Replace("'@/settings/general/users/email-notifications-tab'", "'./users/email-notifications-tab'")
        [IO.File]::WriteAllText((Join-Path $sandbox $file.target), $content)
    }
    [IO.File]::WriteAllText((Join-Path $sandbox 'hooks-shim.ts'), "export { default as useForm } from './use-form';`nexport const useHandleError = () => () => {};`n")
    foreach ($name in @('settings-shim.ts', 'theme-shim.ts', 'shade-shim.ts', 'images-shim.ts', 'errors-shim.ts', 'members-shim.ts', 'tiers-shim.ts', 'helpers-shim.ts', 'components-shim.ts', 'patterns-shim.ts', 'primitives-shim.ts', 'site-shim.ts', 'verify-shim.ts', 'app-shim.ts', 'users-shim.ts', 'framework-shim.ts')) {
        [IO.File]::WriteAllText((Join-Path $sandbox $name), 'export {};')
    }
    foreach ($name in @('account-page.tsx', 'look-and-feel.tsx', 'portal-preview.tsx', 'signup-options.tsx')) {
        [IO.File]::WriteAllText((Join-Path $sandbox $name), 'export default () => null;')
    }
    New-Item -ItemType Directory -Path (Join-Path $sandbox 'navigation') | Out-Null
    [IO.File]::WriteAllText((Join-Path $sandbox 'navigation/navigation-edit-form.tsx'), 'export default () => null;')
    New-Item -ItemType Directory -Path (Join-Path $sandbox 'users') | Out-Null
    foreach ($name in @('profile-tab.tsx', 'social-links-tab.tsx', 'email-notifications-tab.tsx')) {
        [IO.File]::WriteAllText((Join-Path $sandbox "users/$name"), 'export default () => null;')
    }
    [IO.File]::WriteAllText((Join-Path $sandbox 'vitest.config.mjs'), @'
import path from 'node:path';
export default {
  cacheDir: './vite-cache',
  resolve: {
    dedupe: ['react', 'react-dom'],
    alias: [
      { find: '@', replacement: path.join(process.env.PR32433_WORKTREE, 'apps/admin/src') },
      ...Object.entries({
        '@tryghost/admin-x-framework/api/images': 'images-shim.ts',
        '@tryghost/admin-x-framework/api/members': 'members-shim.ts',
        '@tryghost/admin-x-framework/api/tiers': 'tiers-shim.ts',
        '@tryghost/admin-x-framework/api/site': 'site-shim.ts',
        '@tryghost/admin-x-framework/api/email-verification': 'verify-shim.ts',
        '@tryghost/admin-x-framework/api/users': 'users-shim.ts',
        '@tryghost/admin-x-framework/errors': 'errors-shim.ts',
        '@tryghost/admin-x-framework/helpers': 'helpers-shim.ts',
        '@tryghost/admin-x-framework': 'framework-shim.ts',
        '@tryghost/shade/components': 'components-shim.ts',
        '@tryghost/shade/patterns': 'patterns-shim.ts',
        '@tryghost/shade/primitives': 'primitives-shim.ts',
        '@tryghost/shade/app': 'app-shim.ts',
      }).map(([find, file]) => ({ find, replacement: path.resolve(file) })),
    ],
  },
  test: { environment: 'jsdom', globals: true, include: ['*.test.ts', '*.test.tsx'] },
};
'@)
    $env:NODE_OPTIONS = '--max-old-space-size=2048'
    $env:PR32433_WORKTREE = $root
    $env:TEMP = $sandbox
    $env:TMP = $sandbox
    $env:XDG_CACHE_HOME = Join-Path $sandbox 'cache'
    Push-Location -LiteralPath $sandbox
    $pushed = $true
    $node = Join-Path $root 'node_modules/.bin/node.exe'
    $vitest = Join-Path $root 'apps/admin/node_modules/vitest/vitest.mjs'
    & $node --version
    $testArgs = @('run', '--config', 'vitest.config.mjs', '--pool=threads', '--maxWorkers=1', '--no-file-parallelism')
    if ($Filter) { $testArgs += @('--testNamePattern', $Filter) }
    if ($TestFile) { $testArgs += $TestFile }
    & $node $vitest @testArgs
    $result = $LASTEXITCODE
} finally {
    if ($pushed) { Pop-Location }
    if (Test-Path -LiteralPath $sandbox) {
        $target = (Resolve-Path -LiteralPath $sandbox).Path
        $prefix = $parent.TrimEnd('\') + '\.tmp-pr32433-fix-'
        if (!$target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Unexpected sandbox path: $target" }
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
exit $result
