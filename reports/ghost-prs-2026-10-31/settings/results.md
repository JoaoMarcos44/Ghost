# Issue #32421 — validação da correção de salvamento pendente

**Resultado final:** 28 testes passaram em 2 arquivos, com exit 0. Uma edição
feita enquanto o salvamento anterior está pendente fica imediatamente
unsaved, preservando os avisos de alterações não salvas. Um segundo salvamento
simultâneo é bloqueado; após falha do primeiro, a nova edição permanece
disponível e pode ser salva na tentativa seguinte.

O teste do grupo de configurações confirmou que B sobrevive a uma atualização
do contexto com A, a edição permanece aberta após A e fecha depois que B é
salvo. O teste usa o contexto e o hook reais, com a mutação de settings, o
tratador de erro e o estado global de alteração simulados; não exercita
navegador ou API reais. O ciclo não incluiu typecheck completo, pnpm check ou
acceptance de Admin. O lint focado não produziu resultado antes do timeout
descrito no histórico.

Worktree: C:\Users\Nitro\Ghost\.worktrees\fix-settings-pending-save-20261031  
Branch: fix/settings-pending-save-20261031  
Base: 5d4430c8c157990adbd69400f4cee9795037fbbb

## Alterações

- useForm impede salvamentos sobrepostos e compara a versão do formulário antes
  de sinalizar saved. Uma edição durante a operação fica imediatamente
  unsaved; se houver edição ou reset, a operação anterior retorna false.
- useSettingGroup só atualiza os valores locais a partir do contexto fora do
  modo de edição e sincroniza novamente quando a edição fecha.
- Os testes upstream cobrem edição, save sobreposto, reset e falha durante o
  salvamento, além do refresh do contexto e do salvamento posterior de B.

Enquanto A estiver pendente e B estiver unsaved, consumidores que habilitam o
botão somente por saveState podem permitir um clique; a proteção por referência
rejeita a tentativa sobreposta e B permanece pendente para um novo save após A.
O comportamento do timer de indicação saved não foi alterado; a issue #30933 é
separada.

## Validação final

O código foi copiado da worktree para um sandbox temporário dentro dela. O
runner usou Node v22.23.4 e Vitest 4.1.12 instalados na worktree, pool threads,
um worker, NODE_OPTIONS=--max-old-space-size=4096 e NX_DAEMON=false:

~~~powershell
python -c "from pathlib import Path; import sys; p=Path(r'C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31\settings\isolated-runner.md'); s=p.read_text(encoding='utf-8'); exec(s.split('~~~python\n',1)[1].split('\n~~~',1)[0], {'__name__':'__main__'})"
~~~

~~~text
Test Files  2 passed (2)
     Tests  28 passed (28)
VITEST_EXIT_CODE 0
SANDBOX_CLEANUP True
~~~

O runner integral está em [isolated-runner.md](isolated-runner.md). Ele usa um
facade de imports para as dependências externas do grupo. Após os ciclos, não
foram encontrados sandboxes nem processos Vitest ou ESLint da tarefa.
git diff --check retornou exit 0.

## Histórico RED e diagnóstico dos runners

Antes da primeira correção, o RED retornou exit 1 esperado: 4 testes novos
falharam e 23 existentes passaram. As falhas incluíram saved em vez de
unsaved, save sobreposto aceito e o fechamento do grupo após o save antigo.
A primeira correção passou em 27 testes.

A revisão seguinte identificou que manter saving após uma nova edição escondia
a alteração de consumidores que usam saveState === 'unsaved'. O RED dessa
revisão retornou exit 1 esperado: 3 testes falharam com saving em vez de
unsaved antes da conclusão de A; 25 passaram. A alteração final produziu os
28 testes verdes registrados acima.

Uma tentativa inicial, antes de terminar o bootstrap, usou Vitest 4.1.11 da
instalação anterior e atingiu timeout de 90 segundos após RUN, sem resultados.
O sandbox foi removido. Um diagnóstico separado de worker_threads com Node
22.23.4 retornou exit 0; após o bootstrap, os ciclos RED e GREEN executaram
com as dependências da worktree.

Um primeiro ESLint focado foi interrompido para limitar a concorrência. A
tentativa seguinte, sobre cópias dos arquivos de admin-x-framework, usou a
configuração do pacote e --no-cache, mas não produziu resultado antes do timeout
de 90 segundos. Terminou com exit 1 por subprocess.TimeoutExpired e o sandbox
foi removido:

~~~text
C:\Users\Nitro\Ghost\.worktrees\fix-settings-pending-save-20261031\node_modules\.bin\node.exe C:\Users\Nitro\Ghost\.worktrees\fix-settings-pending-save-20261031\apps\admin-x-framework\node_modules\eslint\bin\eslint.js --no-cache --config C:\Users\Nitro\Ghost\.worktrees\fix-settings-pending-save-20261031\apps\admin-x-framework\eslint.config.js src/hooks/use-form.ts test/unit/hooks/use-form.test.ts
~~~

O comando foi executado em diretório temporário contendo as cópias. A
configuração desse pacote usa reactAppConfig sem projectService; ela não é o
lint type-aware do Admin. A causa da espera não foi determinada e uma nova
tentativa não foi iniciada por orientação do orquestrador.