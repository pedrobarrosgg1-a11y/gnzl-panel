# Etapa 9 — lotes e histórico de links na interface

Data: 2026-11-12

## Entrega

- Tela `/lotes` para criar e consultar lotes:
  - criação a partir de uma lista, com `?lista=<id>` preenchendo a origem;
  - criação a partir de produtos escolhidos na busca, com
    `?produtos=1,2,3` e os títulos enviados pelo `state` da navegação;
  - nome, observação e os cinco Sub IDs opcionais;
  - filtros por status e origem com paginação.
- Tela `/lotes/:id` com:
  - faixa de métricas (itens, links gerados, falhas e criação);
  - origem, Sub IDs e data de finalização;
  - botão explícito `gerar links`, sem disparo automático na criação;
  - execução repetida apenas para itens pendentes ou com falha;
  - resultado por item, incluindo código e mensagem de erro;
  - copiar e abrir o link gerado.
- Tela `/links` com histórico paginado:
  - filtros por termo, lote, status, origem e Sub IDs 1–3;
  - link ativo e link substituído identificados;
  - referência ao link que substituiu o anterior;
  - copiar, abrir e regenerar link ativo.
- Regeneração inline: exige alteração de ao menos um Sub ID antes de chamar a
  API, mantendo o link anterior no histórico.
- Modo de seleção na busca:
  - checkbox por produto, mantendo a seleção entre páginas;
  - limite de 200 itens por lote;
  - atalho para criar o lote com os produtos selecionados.
- Cliente de API tipado para lotes e links.
- Utilitários de status, Sub IDs e IDs de produtos, cópia para a área de
  transferência e ícone Lucide `copy` salvo localmente.

## Decisões

- Criar e gerar são passos separados. O lote nasce `pending` e só executa
  quando o usuário pede, permitindo revisar origem e Sub IDs.
- O botão de execução muda de rótulo conforme o estado: `gerar links` no
  primeiro uso e `tentar pendentes` depois de falhas parciais.
- A regeneração compara os cinco slots normalizados no cliente. Sem alteração,
  o formulário bloqueia o envio e explica o motivo sem chamar a API.
- A tela sempre envia os cinco Sub IDs na regeneração; slots esvaziados são
  limpos de forma intencional.
- Erros de conflito da API são exibidos como resposta, sem modal.
- A seleção da busca é estado local da página; a URL carrega apenas os IDs
  necessários para a criação do lote.
- A tela de links usa a URL como fonte da verdade dos filtros, seguindo o
  padrão da busca e das listas.

## Evidências

- `npm run test`: 54 testes em 8 arquivos, todos aprovados.
- `npm run build`: `tsc -b` e `vite build` sem erros (80 módulos).
- Backend: 127 testes aprovados.
- Smoke test com backend real em `127.0.0.1:8000` e Vite em `5174`:
  - lote criado de uma lista de teste com três produtos e Sub ID normalizado;
  - execução terminou `partial` com 2 links gerados e 1 falha simulada;
  - item com falha mostrou mensagem e código `provider_unavailable`;
  - cópia do link confirmada sem modal;
  - histórico filtrado pelo lote mostrou os links ativos;
  - regeneração com Sub ID adicional criou novo link e marcou o anterior como
    substituído;
  - seleção de produto na busca abriu `/lotes?produtos=1` com a origem correta;
  - lote de produto avulso executou e concluiu;
  - filtros combinados e estado vazio do histórico responderam como esperado;
  - console do navegador sem erros.
- Dados temporários do smoke removidos por ID (lotes, itens, links e lista de
  teste), preservando o restante do banco.

## Limites

- Ainda não há testes E2E em Playwright para lotes e links; a etapa 10 cobre
  esse fluxo.
- Lotes não podem ser excluídos pela interface nem pela API atual.
- Lotes em execução não atualizam sozinhos; é preciso recarregar a página.
- O histórico filtra Sub IDs apenas nos três primeiros slots, embora os cinco
  sejam gravados.
- O provedor `shopee` segue não implementado; tudo roda em modo demo.

## Observação de ambiente

Depois de muitas alterações com Fast Refresh, o Vite voltou a servir um módulo
antigo de ícones (erro de export ausente). Reiniciar apenas o processo do Vite
resolveu, sem tocar no backend. O mesmo comportamento já registrado na etapa 8.
