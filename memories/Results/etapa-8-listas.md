# Etapa 8 — listas de produtos na interface

Data: 2026-11-11

## Entrega

- Tela `/listas` para criar e consultar listas, com nome, descrição opcional,
  quantidade de produtos e data de atualização.
- Tela `/listas/:id` com:
  - faixa de métricas (produtos, criação e atualização);
  - edição inline de nome e descrição;
  - confirmação inline de exclusão, sem modal;
  - remoção de produto por linha;
  - estado vazio com atalho para adicionar produtos.
- Modo lista na busca (`/?lista=<id>`): banner com o nome da lista, link para
  o detalhe, saída do modo e botão `+` em cada resultado.
  - Produto já presente aparece como "na lista" e não pode ser adicionado duas
    vezes.
  - O parâmetro `lista` é preservado ao enviar filtros, limpar filtros e
    paginar.
- Cliente de API tipado para listas, incluindo respostas HTTP 204.
- Componentes compartilhados `StateMessage`, `Feedback` e `FormPanel`.
- Utilitário de datas exibindo o horário de Brasília.
- Ícones Lucide `plus`, `pencil`, `trash-2` e `check` salvos localmente.

## Decisões

- A URL continua sendo a fonte da verdade. `?lista=<id>` define o modo de
  adição; sair do modo remove apenas esse parâmetro.
- Criação e edição usam validação local para nome vazio, mas a mensagem de
  conflito de nome vem da API e é exibida como está.
- Exclusão de lista usa confirmação inline em vez de modal, seguindo o padrão
  do projeto de não interromper a navegação.
- Remoção de produto é imediata e reversível pela busca, então não pede
  confirmação.
- Após adicionar um produto, o estado local da lista é atualizado com a
  resposta da API (`items` e `item_count`), sem refazer a busca.
- O modo lista não envia `lista` para a API de produtos: o parâmetro é só de
  navegação.

## Evidências

- `npm run test`: 32 testes em 5 arquivos, todos aprovados.
- `npm run build`: `tsc -b` e `vite build` sem erros.
- Backend: 127 testes aprovados.
- Lighthouse em `/listas` e `/listas/:id`: acessibilidade 100 e boas
  práticas 100. SEO 80 apenas pelo `/robots.txt` do servidor de
  desenvolvimento, como nas etapas anteriores.
- Smoke test com backend real em `127.0.0.1:8000` e Vite em `5174`:
  - lista criada com descrição;
  - detalhe mostrou estado vazio;
  - produto adicionado pelo modo lista e contagem atualizada;
  - nome editado com sucesso;
  - produto removido e estado vazio reapareceu;
  - lista excluída pela confirmação inline;
  - `GET /api/lists` terminou com zero listas.
- Console do navegador sem erros durante o fluxo.

## Limites

- Listas não têm paginação; a API atual devolve todas as listas de uma vez.
- Não há reordenação manual de produtos; a ordem é a de inserção.
- Ainda não há testes E2E em Playwright para este fluxo.
- O editor de lista é inline, não uma página separada; listas muito longas
  continuam rolando horizontalmente junto com a tabela.
- O provedor `shopee` segue não implementado. As credenciais no `.env` não
  mudam o modo de dados enquanto `GNZL_PROVIDER=demo`.

## Observação de ambiente

Após muitas edições com Fast Refresh, o Vite pode manter um módulo antigo em
cache e continuar servindo uma rota anterior mesmo com o arquivo em disco
atualizado. Reiniciar apenas o processo do Vite resolveu; o backend não precisa
ser reiniciado.
