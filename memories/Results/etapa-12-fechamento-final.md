# Etapa 12 - fechamento final da fase 1

Data: 2026-11-12

## Entrega

- Fase 1 marcada como concluída no `README.md` (etapas 0 a 12).
- `docs/architecture/phase-1.md` recebeu:
  - seção de status do encerramento;
  - tabela de critérios de aceitação com a evidência principal de cada um;
  - limitação do provedor oficial reclassificada como fora do escopo da fase.
- Corrigida a lacuna de registro de uso de Sub IDs quando a primeira execução
  do lote falha por completo.

## Correção de comportamento

Antes, o uso dos Sub IDs só era registrado se o lote estivesse em `pending` na
primeira execução. Se todos os itens falhassem e um retry posterior gerasse
links, o autocomplete nunca recebia esses valores.

A decisão passou a ser baseada no resultado acumulado:

```python
should_register_usage = batch.successful_items == 0
```

Assim, o uso é registrado na primeira execução que gerar ao menos um link,
inclusive quando ela é um retry. Depois que o lote tem sucesso, retries não
incrementam a contagem novamente.

- Código: `backend/app/services/link_batches.py`.
- Teste novo:
  `test_usage_is_registered_when_first_run_fails_and_retry_succeeds` em
  `backend/tests/services/test_link_batches.py`.
- Documentação ajustada em `docs/architecture/link-generation.md`.

## Critérios de aceitação verificados

Todos os itens da fase 1 foram mapeados para testes ou documentação:
estrutura/configuração, banco por migrations, contratos do provedor demo,
busca, listas, Sub IDs, lotes, histórico/regeneração e fluxo E2E. A tabela
completa está em `docs/architecture/phase-1.md`.

## Evidências

- Backend: **129 testes aprovados** (128 anteriores + 1 regressão).
- Vitest: **54 testes em 8 arquivos**, aprovados.
- `npm run build`: aprovado, **80 módulos**.
- Playwright: **3 fluxos aprovados em 12,4 s**.
- Banco E2E descartável recriado pelas migrations; banco de desenvolvimento
  não foi tocado.

## Limitações mantidas

- Provedor oficial da Shopee fora do escopo da fase 1; a aplicação segue em
  modo demo.
- Execução de lote síncrona, sem fila ou retry automático com backoff.
- Sem autenticação de usuário; uso restrito a loopback.
- E2E apenas em Chromium desktop.
