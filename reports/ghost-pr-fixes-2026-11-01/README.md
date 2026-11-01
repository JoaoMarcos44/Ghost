# Correções dos três PRs do Ghost

As falhas reproduzidas na [auditoria anterior](../ghost-pr-review-2026-11-01/README.md) foram corrigidas e publicadas nas três branches. As mudanças usam verificações locais de estado, composição do HTML e lotes pequenos nas consultas. Mantêm a estrutura existente, sem abstrações gerais ou funcionalidades especulativas.

| PR                                                     | Correção                                                                                                                     | Validação focada                                                                                                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| [#32432](https://github.com/TryGhost/Ghost/pull/32432) | Preserva espaços entre palavras formatadas no e-mail do toggle.                                                              | 56 testes; a mesma regressão também passou no projeto unitário real do Core adaptado ao sandbox.                                   |
| [#32433](https://github.com/TryGhost/Ghost/pull/32433) | Preserva edições novas diante de respostas antigas, respeita `false` antes de fechar e impede feedback de saves sobrepostos. | 47 testes em 8 arquivos; 16 deles repetidos após ajustes de lint nos testes.                                                       |
| [#32434](https://github.com/TryGhost/Ghost/pull/32434) | Limita parâmetros SQL com lotes de 400 membros e 400 labels; valida contagens sem exigir `action`.                           | Core: 71; framework: 43, dos quais 5 repetidos após o ajuste equivalente do schema. Rollback de 102 relações confirmado em SQLite. |

As execuções adicionais e repetidas não devem ser somadas como casos distintos. Todos os commits de testes e implementação passaram pelos hooks originais. O push foi normal e atômico, sem force push ou merge.

## Compatibilidade e bloqueio de merge

Referência de main: `3b395b6b082bb995bc8dc8d7b648fea7732fe839`, confirmada novamente com `git fetch origin main`. Os três commits mesclam individualmente e em conjunto sem conflitos. Árvore combinada: `b9e69e2a3fb484830f4c869dba287e9b56567408`.

| PR     | Commit publicado                           |
| ------ | ------------------------------------------ |
| #32432 | `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef` |
| #32433 | `1958aa6821284e1caba9c6cf88c222753d6aacf8` |
| #32434 | `1cdac3b534035e02d995160c0b37d330e47b5ea5` |

A formatação global passou em 7.254 arquivos e o Oxlint também passou. O [typecheck oficial do framework](validation/framework-types.md) passou na árvore combinada após compilar as declarações reais dos sete pacotes internos faltantes e de Shade. O `pnpm check` completo parou ao iniciar os plugins do Nx por limite de caminho de socket no Windows, antes das etapas seguintes de teste. [Resultado completo](validation/integrated.md).

A primeira tentativa de formatação apontou 4.776 arquivos; um probe confirmou que `git archive` convertia LF de main para CRLF pela configuração Windows. A preparação foi corrigida com `git -c core.autocrlf=false archive`, sem reformatação dos fontes. Não se atribui esse primeiro resultado ao código upstream.

Após o push, o GitHub confirmou os novos SHAs, `mergeable: true` e `mergeable_state: blocked`. **CI** e **Tinybird** dos novos commits continuam em **`action_required`** e precisam de autorização de um mantenedor. A conta disponível tem apenas leitura no upstream; alterações no código não removem essa exigência.

## Limites

- Settings usa APIs, contexto e UI simulados. Não comprova a ordem real do React Query, atalhos no navegador, backend ou mudança de slug/404 de User Detail. A garantia limita-se aos consumidores testados.
- Não houve testes de navegador, entrega real de e-mail ou HTTP/MySQL de labels. SQLite não substitui essas verificações.
- O lote SQL limita parâmetros por consulta, mas mantém a seleção e as relações em memória na transação. Não houve benchmark de latência ou memória em volume de produção.
- A integração reutiliza dependências instaladas. TypeScript e Zod coincidem com main, mas não houve instalação nova do lockfile integrado. O Windows também impediu a criação dos symlinks de skills no sandbox.
- O HTML de e-mail mantém o comportamento testado, mas espaços estruturais mudaram. A comparação opcional byte a byte e seu resultado estão preservados na evidência.

Os sandboxes desta rodada foram removidos e os processos de teste encerrados. O sandbox histórico de settings cuja exclusão foi rejeitada pela revisão automática foi preservado, sem nova tentativa; ele não integra as alterações publicadas.

## Evidências e infográficos

- [Toggle: solução](pr-32432/summary.md), [evidência](pr-32432/evidence.md) e [infográfico](../ghost-pr-review-2026-11-01/pr-32432/infographic_report.md).
- [Settings: solução](pr-32433/summary.md), [evidência](pr-32433/validation.md) e [infográfico](../ghost-pr-review-2026-11-01/pr-32433/infographic_report.md).
- [Labels: solução](pr-32434/summary.md), [evidência](pr-32434/evidence.md) e [infográfico](../ghost-pr-review-2026-11-01/pr-32434/infographic_report.md).

Os relatórios anteriores são históricos e identificam os SHAs auditados. Recomendações já corrigidas nesses registros não descrevem os commits novos. Os runners usam caminhos do ambiente Windows auditado, que devem ser ajustados em outro ambiente, incluindo a localização temporária das declarações Shade.
