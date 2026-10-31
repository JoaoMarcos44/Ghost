# Resultado parcial da validação

Executado em sandbox para `fix-toggle-html-roundtrip-20261031`, usando Node
22.23.4 e o pnpm instalado, sem instalar pacotes:

1. `pnpm check`: **exit 1** em `format:check`. Oxfmt informou problemas em
   4.763 dos 7.241 arquivos verificados, incluindo muitos arquivos não alterados,
   e encerrou em 41.774 ms. A execução parou antes de lint e testes. O motivo
   dos problemas globais ainda não está estabelecido; o checkout usa
   `core.autocrlf=true`, mas não foi confirmado que isso explique o resultado.
2. `pnpm exec oxfmt --check` dos arquivos alterados: **exit 1** em
   `koenig/kg-html-to-lexical/test/html-to-lexical.test.ts`. Oxfmt informou
   apenas dois arquivos verificados; o resultado não prova formatação dos
   arquivos que a ferramenta ignorou. Depois desse resultado, o hook do toggle
   formatou o arquivo e passou, conforme informado pelo orquestrador.

Oxfmt informou **12 threads**, apesar dos limites aplicados a Node, Nx e Vitest.
É necessário limitar explicitamente o paralelismo nativo antes de nova execução.

A limpeza recebeu `PermissionError: [WinError 5] Acesso negado` em
`.git/objects/00/02059ecbed7cd6ee1bbbe5d10e324c2808196d` dentro de
`C:\Users\Nitro\Ghost\.tmp-sandbox-validation-661554b6e7`. A inspeção do
arquivo confirmou os atributos `ReadOnly, Archive`. Após orientação do
orquestrador, a rotina de remoção foi corrigida para desvincular junctions sem
percorrê-las e retirar o atributo somente leitura apenas de arquivos dentro do
sandbox. A limpeza terminou com **exit 0** e removeu o sandbox. O processo do
runner terminou e não restou processo `run_checks.py toggle` ativo.

`pnpm check` **não foi executado** nas worktrees settings e member/labels. A
versão posterior do runner com `git archive` não foi executada. Junctions de
dependências externas não impõem acesso somente de leitura; caches e saídas
foram configurados para o sandbox, mas não há barreira de escrita na instalação
compartilhada.

## Declarações Shade para hooks

Com fonte Shade rastreada e dependências existentes ligadas no sandbox, passaram:

- `pnpm exec tsc -p tsconfig.declaration.json` — exit 0.
- `pnpm exec tsc-alias -p tsconfig.declaration.json` — exit 0.
- `node scripts/check-declarations.ts` — exit 0.

O arquivo `utils.d.ts` exporta `useGlobalDirtyState`, cuja declaração existe em
`hooks/use-global-dirty-state.d.ts`. Os arquivos são resultados reais do build,
sem stubs. Conforme informado pelo orquestrador, os hooks de settings e labels
terminaram com exit 0 e as duas junctions das worktrees foram removidas. Depois
disso, o sandbox `.tmp-sandbox-validation-shade-d6ff114bad` foi removido com
exit 0. Nenhum processo desta subtarefa permanece em execução.

