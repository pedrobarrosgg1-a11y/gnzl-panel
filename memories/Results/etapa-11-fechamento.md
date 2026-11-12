# Etapa 11 - revisão de fechamento da fase 1

Data: 2026-11-12

## Escopo da revisão

- Configuração e segurança: `.env`, `.env.example`, CORS, logs e exposição de
  credenciais.
- Aderência ao `DESIGN.md`: tokens, tipografia, ícones, estados, foco,
  responsividade e `prefers-reduced-motion`.
- Consistência entre código, contratos da API e documentação.
- Execução completa das suítes após as correções.

## Correções aplicadas

- `.env.example`: domínio da Open API corrigido de `ffiliate` para
  `affiliate`, igual ao padrão de `Settings`.
- `docs/architecture/data-model.md`: incluída a coluna `product_url` em
  `products`, que já existia no modelo e é usada na criação de lotes.
- `README.md`: etapas 11 e 12 separadas (11 concluída, 12 pendente), referência
  à visão da fase 1 e variáveis `GNZL_DATABASE_URL` e `GNZL_SHOPEE_API_BASE` na
  tabela de configuração.
- Criado `docs/architecture/phase-1.md` com camadas, fluxos, integridade,
  segurança, testes e limitações da fase.

## Verificações sem achados

- Nenhum `TODO`, `FIXME`, `console.log`, `debugger`, gradiente ou sombra no
  código auditado.
- Cores fora de `tokens.css`: nenhuma. Ícones são SVGs da Lucide em
  `frontend/src/assets/icons/`.
- CORS habilitado apenas em `dev`, restrito às origens `localhost:5173` e
  `127.0.0.1:5173`, sem credenciais. Os testes cobrem a restrição e a ausência
  de CORS em `prod`.
- `/api/config` não devolve credenciais; o teste existente confirma que
  `app_id` e `secret` não aparecem na resposta.
- Erros inesperados são registrados no servidor e devolvidos sem detalhes
  internos; o teste confirma que a mensagem original não vaza.
- `.env` não é versionado; apenas `.env.example` está no Git.
- Links externos usam `rel="noreferrer noopener"`.
- Layout verificado em 390 px e 1280 px nas telas de busca, listas, lotes e
  links. Sidebar vira menu móvel, tabelas continuam legíveis, foco e skip link
  presentes.

## Evidências

- Backend: 128 testes aprovados.
- Vitest: 54 testes em 8 arquivos, aprovados.
- `npm run build`: aprovado, 80 módulos.
- Playwright: 3 fluxos aprovados em 12,6 s, com banco E2E descartável.
- Suite Python emite apenas o aviso de depreciação do Starlette sobre `httpx`;
  não afeta os testes.

## Limitações

- Provedor oficial da Shopee continua não implementado; a aplicação permanece
  em modo demo.
- E2E cobre só Chromium em viewport desktop. A checagem mobile foi visual, sem
  teste automatizado dedicado.
- O lint Python não faz parte da suíte; a revisão foi estática e por testes.
