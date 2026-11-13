# Etapa 19a — provedor oficial da Shopee (busca e links)

Data: 2026-11-12

## Entrega

`GNZL_PROVIDER=shopee` passou a montar um provedor real, sem fallback para demo:

- busca de produtos por palavra-chave, com paginação e ordenação;
- geração de link curto com até 5 Sub IDs;
- capacidades declaradas em `/api/config`;
- filtros não suportados escondidos no frontend e recusados com `422` no
  backend.

Arquivos principais:

- `backend/app/providers/shopee/client.py`
- `backend/app/providers/shopee/provider.py`
- `backend/app/providers/capabilities.py`
- `backend/app/providers/registry.py`
- `backend/app/services/products.py`
- `backend/app/schemas/system.py`
- `backend/app/api/system.py`
- `frontend/src/pages/SearchPage.tsx`
- `frontend/src/types/api.ts`
- `docs/architecture/shopee-provider.md`
- `backend/tests/providers/test_shopee.py`

## Decisões

- Assinatura sobre os **bytes exatos** do JSON, em UTF-8 compacto.
- `listType: 1` explícito; `listType: 0` causou `10000`.
- `sortType` documentado: 1 relevância, 2 vendidos, 3 maior preço, 4 menor
  preço, 5 comissão.
- `total = None`: a API não informa total; não inventar número.
- `category = None`: `productCatIds` são IDs, não nomes.
- Retry com backoff só em queries. Mutation nunca é repetida automaticamente.
- Capacidades como contrato único entre backend, `/api/config` e interface.

## Evidências

- `pytest`: **186 testes aprovados** (164 anteriores + 22 novos).
- `vitest`: **55 testes aprovados** (54 anteriores + 1 novo).
- `npm run build`: aprovado.
- Validação manual real: busca com `keyword="fone"` retornou 3 itens, com
  preço `3671` centavos, comissão `300` bp e avaliação `500`; `has_next=true`.
- Link real gerado com Sub ID `validacao19a` (`s.shopee.com.br`, 34
  caracteres), sem gravar no banco local.
- `/api/config` em modo shopee retornou as capacidades corretas e nenhuma
  credencial.

## Limitações

- Conversões (19b) ainda não sincronizadas.
- Sem catálogo de nomes de categoria.
- Sem total de resultados.
- `10000` continua intermitente sob muitas chamadas; após 3 tentativas vira
  `503 provider_unavailable`.
