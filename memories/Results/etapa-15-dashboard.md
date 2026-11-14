# Etapa 15 — normalização compartilhada e dashboard

Data: 2026-11-13

## Entrega

Duas frentes, nesta ordem:

1. CSV e Shopee passaram a normalizar os pedidos pelas mesmas regras, em
   `backend/app/core/conversion_rules.py`.
2. `GET /api/dashboard` entrega métricas agregadas por origem e período, com
   comparação contra o período anterior, série diária e rankings.

### Normalização compartilhada

| regra | antes | depois |
|---|---|---|
| `status_group` ausente no CSV | `unknown` | derivado do status bruto |
| Sub ID com `/` | CSV removia, Shopee trocava por `-` | `a-z0-9-` canônico nos dois |
| quantidade ausente | CSV 1, Shopee 0 | 1 nos dois |
| valores negativos | CSV aceitava | erro de linha nos dois |
| canal | texto cru | token de dispositivo em maiúsculas |
| título/status longos | CSV rejeitava, Shopee cortava | corte nos dois, original em `raw_data` |

### Dashboard

- `source` obrigatório (`demo`, `shopee` ou `csv`);
- período em dias locais (UTC-3 fixo), padrão de 30 dias terminando hoje;
- janela máxima de 366 dias;
- vendas/comissão/pedidos apenas `approved`; pedidos distintos por
  `external_order_id`; cliques todas as linhas;
- conversão em pontos-base (nula sem cliques) e ticket médio em centavos (nulo
  sem pedidos);
- comparação com o período anterior de mesma duração, com `absolute` e
  `variation_bp` (nulo quando o anterior é zero);
- série diária zero-preenchida;
- rankings de Sub IDs e itens, até 10 por comissão.

Arquivos principais:

- `backend/app/core/normalization.py`
- `backend/app/core/conversion_rules.py`
- `backend/app/services/normalization.py`
- `backend/app/services/csv_import.py`
- `backend/app/providers/shopee/provider.py`
- `backend/app/core/time.py`
- `backend/app/repositories/dashboard.py`
- `backend/app/services/dashboard.py`
- `backend/app/schemas/dashboard.py`
- `backend/app/api/dashboard.py`
- `backend/app/main.py`
- `backend/tests/test_conversion_rules.py`
- `backend/tests/services/test_conversion_normalization.py`
- `backend/tests/services/test_dashboard.py`
- `backend/tests/api/test_dashboard.py`
- `docs/architecture/dashboard.md`

## Decisões

- A classificação de status usa tokens em inglês **e português**. "Aprovado"
  não casava com o token `approv` (uma letra `p` a mais) e caía em `unknown`;
  por isso a lista inclui `aprov`, `conclu`, `pend`, `enviad`, `entreg`,
  `reembols` e `estorn`, além de `não pago`/`nao pago` antes de `pago`.
- O `status_group` declarado no CSV prevalece sobre a derivação. Valor inválido
  é erro de linha, não adivinhação.
- Campos de identidade (`order_id`, `item_id`) são validados; campos
  descritivos são cortados. O original fica em `raw_data`, então o corte não
  esconde dado.
- Canal só vira maiúsculas quando é um token de dispositivo conhecido. Texto
  livre (`Instagram`) é preservado e não vira `INSTAGRAM`.
- O fuso local usa offset fixo de -3 horas porque o Brasil não tem horário de
  verão desde 2019 e `tzdata` não existe no Windows por padrão.
- O recorte diário usa `date(coluna, '-3 hours')` do SQLite. É específico do
  banco do projeto, mas evita trazer todas as linhas para agrupar em Python.
- `orders` no dashboard é `count(distinct external_order_id)`: um pedido com
  vários itens não infla a contagem.
- Sem base anterior (`previous = 0`), a variação é `null`. Mostrar 100% ou ∞
  seria inventar informação.
- Rankings de Sub IDs partem dos pedidos aprovados; Sub ID só com cliques não
  aparece. O grupo `null` (sem Sub ID) aparece normalmente.
- Título do ranking de itens é o mais recente conhecido, buscado em uma segunda
  consulta para os 10 itens — `max(title)` seria arbitrário.

## Evidências

- `pytest`: **302 testes aprovados** (228 anteriores + 74 novos).
- `vitest`: **55 testes aprovados** (nenhum arquivo de frontend foi alterado).
- `npm run build`: aprovado.
- Validação com banco descartável criado pelas migrations, sem tocar
  `data/gnzl.db` nem o `.env`:
  - importação CSV de um pedido aprovado e um clique;
  - `GET /api/dashboard?source=csv&start=...&end=...` respondeu `200`;
  - métricas, série diária e rankings conferidos com os valores importados;
  - origem `shopee` no mesmo banco retornou zeros, confirmando o isolamento.

## Limitações

- Metas (etapa 17) ainda não aparecem no dashboard.
- Não há filtro por canal ou por Sub ID; rankings são o recorte disponível.
- O offset fixo de -3 horas precisa ser revisto se o horário de verão voltar.
- A tela e o gráfico são a etapa 16.
