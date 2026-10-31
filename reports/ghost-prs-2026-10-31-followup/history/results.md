# Histórico de assinantes — validação

Base: `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b`.

O total da resposta continua refletindo os assinantes atuais. Para reconstruir
a série de um intervalo encerrado no passado, o serviço agora também desfaz o
saldo dos eventos posteriores ao limite final, filtrando pela mesma newsletter
e excluindo os membros com email desabilitado. O limite usa o fuso solicitado;
eventos exatamente no fim permanecem incluídos no intervalo. Sem `date_to`, não
é feita a consulta adicional.

## Validação

O runner extrai `git archive HEAD`, sobrepõe os arquivos alterados, usa as
dependências instaladas na worktree e mantém temporários, logs e cache do Vitest
no sandbox. Ele remove as junctions e o sandbox depois da execução. Node
22.23.4, heap máximo de 4096 MB, `UV_THREADPOOL_SIZE=1`, Vitest com pool
`threads`, um worker e timeout de 180 segundos para o processo do teste.

```powershell
python C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31-followup\history\runner.py red
python C:\Users\Nitro\Ghost\reports\ghost-prs-2026-10-31-followup\history\runner.py green
```

- **RED:** testes de `getNewsletterSubscriberStats` com a implementação da
  base e as regressões atualizadas: **4 falharam, 7 passaram, 45 ignorados**;
  exit 1 esperado. As quatro falhas foram de valores históricos: assinatura
  posterior, cancelamento posterior, intervalo sem eventos e limite no fuso
  `Asia/Kolkata`. Não houve falha de inicialização.
- **GREEN:** arquivo oficial `posts.test.js` completo com a correção: **56
  passaram**, exit 0. Inclui controles de total atual, ausência de `date_to`,
  filtro de newsletter, email desabilitado e evento no limite inclusivo.
- Ambas as execuções registraram `SANDBOX_CLEANUP True` após o processo do teste
  terminar.

As consultas foram exercitadas com o SQLite dos testes unitários; MySQL e a API
HTTP completa não foram executados. O agrupamento existente por data UTC e o
preenchimento de dias com fusos horários não foram alterados.
