# Etapas 6 e 7 — fundação do frontend e busca de produtos

Data: 2026-11-09

## Entrega

- Fundação Vite 8 + React 19 + TypeScript + React Router 7 (modo biblioteca).
- Layout com barra lateral fixa de 248 px, menu recolhível no mobile e rodapé
  com estado do sistema (modo demo + versão).
- Tela real de busca: termo, categoria, ordenação, faixa de preço e comissão
  mínima; tabela de produtos, paginação, estados de carregamento, erro e vazio.
- Sinalização explícita do modo demo no cabeçalho, na barra lateral e acima
  dos resultados.
- Placeholders honestos para listas, lotes e links, indicando a etapa em que
  cada tela entra.
- Ícones Lucide salvos em `frontend/src/assets/icons` e importados como
  componentes via `vite-plugin-svgr`.
- Fontes Syne e Inter hospedadas localmente via `@fontsource`.
- Tokens e componentes globais derivados do `DESIGN.md`.

## Decisões

- A URL (`useSearchParams`) é a fonte da verdade da busca. O formulário é
  derivado dela, então voltar/avançar no navegador repõe os filtros.
- Toda requisição usa `AbortController`; respostas antigas não sobrescrevem
  buscas mais recentes.
- Erros da API passam por `ApiError`, que lê o envelope `{"error": {...}}` do
  backend e preserva `code`, `details` e `request_id`.
- Valores continuam em centavos e pontos-base no transporte. A conversão para
  reais/percentual acontece apenas na borda da interface.
- O botão de ordenação é um `select` explícito em vez de cabeçalhos clicáveis,
  o que deixa a ordenação visível e acessível por teclado.

## Evidências

- `npm run test`: 21 testes em 3 arquivos, todos aprovados.
- `npm run build`: `tsc -b` e `vite build` sem erros.
- Lighthouse na tela de busca: acessibilidade 100 e boas práticas 100.
- Smoke test com backend real:
  - busca `fone` retorna 2 produtos (o termo também casa com "microfone");
  - categoria `Casa` retorna 7;
  - preço mínimo R$ 100 + comissão 10% retorna 5, ordenados por comissão;
  - paginação de 31 resultados gera 11 linhas na página 2;
  - busca `zzz` mostra o estado vazio;
  - menu mobile abre e fecha com Escape.
- Backend: 127 testes aprovados (nenhuma alteração de comportamento).

## Limites

- Ainda não existem testes E2E em Playwright; a validação de navegador foi manual.
- O backend ainda não serve `frontend/dist`; em desenvolvimento são dois
  processos (API + Vite).
- Listas, lotes e links ainda são telas de "em construção" (etapas 8 e 9).
- Em telas estreitas a tabela rola horizontalmente; as colunas não são ocultadas.
- Não há retry automático no frontend: a falha mostra a mensagem e um botão
  "tentar novamente".
