# Revisão aprofundada dos três PRs abertos em TryGhost/Ghost

Data: 1 de novembro de 2026. Escopo: os três PRs abertos de JoaoMarcos44. A auditoria examina os commits indicados, sem alterar código de produto nem considerar os checks do bot como aprovação de testes.

| PR | Solução e achados | Avaliação do review |
| --- | --- | --- |
| [#32432 — toggle HTML](https://github.com/TryGhost/Ghost/pull/32432) | A correção preserva formatação no caminho web. Regressão confirmada na composição com o renderer de e-mail: `Hello world` vira `Helloworld` entre elementos inline. | A explicação do CodeRabbit é correta, mas “Minimal” deixa passar um caso real. Os alertas ast-grep sobre leitura de outerHTML nos testes não demonstram XSS. |
| [#32433 — Save pendente](https://github.com/TryGhost/Ghost/pull/32433) | A proteção funciona para o grupo comum. Consumidores que ignoram false e setters de respostas antigas ainda permitem perda de edição. Há diferença nova no segundo Save rejeitado; parte das perdas já existia na base. | Os dois apontamentos de navegação são pertinentes. A sugestão de guard precisa contemplar estado dirty com erro; o escopo deve incluir outros consumidores, como Design. |
| [#32434 — remoção de labels](https://github.com/TryGhost/Ghost/pull/32434) | A seleção estável e o rollback funcionam no probe. Limite de parâmetros SQLite em seleção grande e contrato de resposta divergente merecem tratamento. | A análise transacional e o alerta de validação em runtime são pertinentes. “Minimal” não cobre o limite reproduzido nem substitui browser/MySQL/HTTP. |

## Documentação

As descrições originais explicam causa, solução, testes e limitações com bons links fixados em commit. Porém, os três PRs já estão `isDraft=false`, enquanto o texto ainda os chama de Draft. A documentação também precisa delimitar o caminho web do toggle, o contrato de false no formulário e o formato real da resposta/contagem de relações da operação de labels.

Relatórios detalhados, referências de código fixadas nos commits e reprodução:

- [Toggle: auditoria](pr-32432/audit.md) · [infográfico](pr-32432/infographic_report.md).
- [Settings: auditoria](pr-32433/audit.md) · [validação](pr-32433/validation.md) · [infográfico](pr-32433/infographic_report.md).
- [Labels: auditoria](pr-32434/audit.md) · [infográfico](pr-32434/infographic_report.md).

Cada diretório contém o snapshot público da consulta, status, fonte dos probes, prompt e `infographic.png`. Os infográficos explicam arquitetura, problema e solução pretendida; os relatórios qualificam os comportamentos ainda incorretos. Foram gerados com a ferramenta nativa, revisados visualmente e corrigidos tecnicamente. O helper foi executado diretamente com Python, sem uv.

## Validação realizada nesta auditoria

| Área | Resultado novo | Limite |
| --- | --- | --- |
| Toggle | 8 cenários na base e 8 no head, exit 0 | Conversor e renderer reais; helpers do editor; sem entrega de e-mail ou navegador |
| Settings | 8 casos totais comparando base/head, exit 0 | Hooks reais, API/contexto controlados; callback do modal representado no harness, sem router real |
| Labels | Probe de seleção, payload, rollback, serializer e limite SQLite, exit 0 | Módulos reais com filtro SQL adaptado; sem HTTP/MySQL/browser |

Os testes de observação passam porque verificam também a presença dos defeitos descritos. Isso não significa que todos os comportamentos estão corretos. Os 170 testes citados na documentação anterior não foram reexecutados nesta rodada e não devem ser somados aos cenários novos como uma suíte única.

No snapshot, os checks verdes são **Label Issues & PRs** e **CodeRabbit**. Não há aprovação humana registrada nem evidência de build/test de produto nesses checks. `pnpm check`, acceptance e MySQL/HTTP continuam pendentes conforme o escopo de cada PR. O PR relacionado #32333 trata do picker de custom fields, não é uma correção substituta deste hook compartilhado.

## Ambiente e limpeza

Os testes usaram Node 22.23.4, no máximo um worker por suíte e limite de heap de 2048 MB. Os sandboxes das execuções concluídas foram removidos e não restaram processos da tarefa.

Uma tentativa inicial de settings iniciou inesperadamente a verificação/instalação de dependências do pnpm e foi interrompida. A causa exata não foi estabelecida. A execução posterior invocou diretamente o Node e o Vitest já instalados e passou. O sandbox inicial `.tmp-pr32433-probe-af6a3ab5bb37412e8e428eb977b8a7d2`, dentro de `apps/admin` da worktree de settings, permanece: a revisão automática de aprovação rejeitou duas remoções com “blocked by policy”. Não houve tentativa de contorno. Os detalhes estão no relatório de settings.

## Recomendação

Antes de merge, corrigir a composição toggle → e-mail e integrar o contrato de Save aos consumidores afetados. Para labels, fechar o contrato de resposta, decidir o tratamento do limite de consulta e executar as validações de integração pendentes. Os achados preexistentes estão separados dos efeitos novos para não atribuir ao PR problemas que ele não criou.

