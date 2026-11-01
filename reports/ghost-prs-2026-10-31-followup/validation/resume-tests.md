# Validação focada dos commits finais

As três worktrees estavam sem alterações rastreadas. Os runners anteriores foram
executados em sandboxes descartáveis, com Node **v22.23.4** da respectiva
worktree, Vitest **v4.1.12**, heap Node de 4096 MB, um worker e instalação
automática do pnpm desativada. Tempos abaixo são os informados pelo Vitest.

| Correção e commit | Teste | Resultado final |
| --- | --- | --- |
| Paginação `c3c35ad9e01cb2db160308e8d4286d7cdb848d77` | `test/unit/frontend/helpers/get.test.ts` | **59/59**, exit **0**, 21,67 s |
| Produto `cd9dcd627bfdb151a376fcc2a6eaaf1bc085ecdb` | `test/nodes/product.test.ts` | **30/30**, exit **0**, 4,88 s |
| Produto `cd9dcd627bfdb151a376fcc2a6eaaf1bc085ecdb` | `test/html-to-lexical.test.ts` | **39/39**, exit **0**, 3,91 s |
| Histórico `54fe601764701dbc7eb3ec8ac3ec027d28f8955e` | `test/unit/server/services/stats/posts.test.js` | **56/56**, exit **0**, 14,25 s |

Comandos de teste efetivamente executados dentro das cópias isoladas:

```text
pnpm exec vitest run test/unit/frontend/helpers/get.test.ts --pool=threads --maxWorkers=1 --no-file-parallelism --testTimeout=60000
pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism test/nodes/product.test.ts
pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism test/html-to-lexical.test.ts
pnpm exec vitest run test/unit/server/services/stats/posts.test.js --pool=threads --maxWorkers=1 --no-file-parallelism
```

Na primeira execução da paginação, com `--testTimeout=15000`, **58 passaram e
1 falhou**, exit **1**, duração **93,77 s**. O teste preexistente `general error
handling > should handle error from the API` excedeu 15 s; setup e importação
totalizaram 72,44 s. A única repetição, com 60 s por teste, passou conforme a
tabela. A hipótese para o timeout é inicialização lenta no host; não se
estabeleceu uma causa definitiva.

Na primeira execução do produto, `product.test.ts` passou **30/30**, exit **0**,
em 45,74 s, mas o wrapper retornou **1** e interrompeu antes do conversor porque
sua regex não reconheceu a saída com cores ANSI. O runner foi repetido uma vez
com cores desativadas e normalização de ANSI; os dois processos de teste e o
wrapper retornaram **0**.

Os runners usados são os documentados em [paginação](../pagination/results.md),
[produto](../product/reproduce.md) e [histórico](../history/runner.py), adaptados
em memória para apontar Node, TEMP, perfil, diretórios de configuração e caches
para o contexto descrito acima; o lint do runner de paginação não foi refeito.
As configurações Vite/Vitest apontaram os caches para o sandbox, e o cache de
compilação do Node foi desativado. O teste de histórico usa SQLite em memória.

Os cinco sandboxes das suítes reportaram limpeza bem-sucedida; seus caminhos
absolutos foram conferidos e já não existiam após as execuções. `Get-Process`
não encontrou processos `node` ou `esbuild` ao final. Os logs temporários foram
removidos com os sandboxes; nenhum artefato anterior foi removido.

As junções de dependências foram conferidas, mas apontam para instalações fora
do sandbox, incluindo o store compartilhado. Os redirecionamentos de cache não
impõem acesso somente de leitura, e não houve monitoramento de escrita em nível
de sistema; portanto esta execução não comprova ausência de escritas através
das junções. Não foram executados E2E, build nem `pnpm check` global nesta
retomada; o timeout anterior do check está documentado em [results.md](results.md).
