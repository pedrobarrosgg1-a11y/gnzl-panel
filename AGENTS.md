# AGENTS.md — Gnzl Achados

## 1. IDENTIDADE DO PROJETO

Você está trabalhando no **Gnzl Achados**, uma ferramenta local para gerenciamento de atividades de afiliados da Shopee Brasil.

O projeto tem como objetivo facilitar:

- Descoberta de produtos e oportunidades de comissão.
- Geração de links de afiliado em lote.
- Organização de campanhas através de Sub IDs.
- Acompanhamento de cliques, pedidos e comissões.
- Organização de materiais de divulgação.
- Automação de divulgação através de APIs oficiais.

O sistema é desenvolvido para uso pessoal e local.

Priorize confiabilidade, simplicidade, organização e facilidade de manutenção.

Não transforme o projeto em uma plataforma SaaS genérica.

---

## 2. LEITURA OBRIGATÓRIA DE CONTEXTO

Antes de iniciar uma tarefa relevante, consulte os documentos relacionados ao trabalho.

### Documentos principais

- `DESIGN.md`: referência obrigatória para qualquer trabalho visual.
- `README.md`: informações gerais e instruções de execução.
- `docs/architecture/`: arquitetura e decisões técnicas vigentes.
- `memories/INDEX.md`: índice dos conhecimentos acumulados.
- `AGENTS.md`: regras permanentes de desenvolvimento.

Consulte também as memories específicas relacionadas à tarefa.

Não presuma que uma implementação anterior está correta apenas porque já existe no código.

Inspecione a implementação antes de alterá-la.

### Skills

Consulte as skills disponíveis em `skills/` e utilize aquelas que forem realmente pertinentes.

Não carregue ou utilize skills sem necessidade.

Não crie novas skills genéricas apenas para aumentar a quantidade de recursos disponíveis.

---

## 3. REGRAS DE DESENVOLVIMENTO

### Código

- Escreva código claro, tipado e organizado.
- Prefira soluções simples em vez de abstrações desnecessárias.
- Evite duplicação de lógica.
- Separe responsabilidades entre componentes, serviços, repositórios e provedores.
- Utilize nomes de funções, variáveis e arquivos que expressem claramente sua finalidade.
- Comente decisões não óbvias, não cada linha de código.
- Trate erros explicitamente.
- Não utilize soluções provisórias como se fossem implementações definitivas.
- Não deixe funcionalidades incompletas escondidas atrás de interfaces aparentemente funcionais.

### Integridade do projeto

Antes de criar um arquivo ou componente, verifique se já existe algo equivalente.

Antes de refatorar, compreenda as dependências da implementação atual.

Não reescreva módulos inteiros quando uma alteração localizada resolver o problema.

Não remova funcionalidades existentes sem necessidade e autorização.

Não altere silenciosamente contratos entre frontend e backend.

Quando uma mudança exigir alteração de contratos, atualize os consumidores e os testes correspondentes.

### Dependências

Instale somente dependências necessárias.

Antes de adicionar uma biblioteca, verifique se o problema pode ser resolvido com as tecnologias já disponíveis.

Não adicione bibliotecas redundantes.

Não substitua tecnologias da stack sem justificar a necessidade.

---

## 4. STACK TECNOLÓGICA

### Backend

- Python.
- FastAPI.
- SQLite.
- SQLAlchemy 2.
- Pydantic.
- HTTPX.
- Configuração por variáveis de ambiente.
- Pytest.

### Frontend

- React 19.
- TypeScript.
- Vite 8.
- React Router 7 no modo de biblioteca.
- CSS modular.
- Motion (`motion/react`).
- Chart.js.
- LocalStorage para preferências e estados temporários.

### Testes

- Pytest: backend.
- Vitest: testes unitários do frontend.
- Playwright: testes E2E.

Verifique a compatibilidade das versões antes de instalar dependências.

Não substitua versões solicitadas silenciosamente.

Se houver incompatibilidade, explique o problema e apresente uma alternativa fundamentada.

---

## 5. ARQUITETURA E RESPONSABILIDADES

Mantenha o frontend e o backend separados.

### Backend

Responsabilidades:

- API REST.
- Regras de negócio.
- Integrações externas.
- Validação de dados.
- Persistência.
- Tratamento de erros.
- Sincronizações.

Organize o código por responsabilidades:

- `api/`: endpoints.
- `schemas/`: validação e contratos de dados.
- `services/`: regras de negócio.
- `providers/`: fontes de dados.
- `repositories/`: persistência e consultas.
- `models/`: entidades do banco.
- `core/`: configurações e infraestrutura.

Os endpoints não devem concentrar regras de negócio complexas.

### Frontend

Responsabilidades:

- Apresentação dos dados.
- Navegação.
- Formulários.
- Interações.
- Estados de carregamento e erro.
- Comunicação com o backend.

Organize o código em:

- `pages/`: páginas.
- `components/`: componentes reutilizáveis.
- `layouts/`: estruturas de navegação.
- `services/`: comunicação com a API.
- `hooks/`: lógica reutilizável.
- `types/`: tipagens.
- `styles/`: estilos.
- `assets/`: recursos visuais.

Não misture regras de negócio do backend com componentes React.

O frontend nunca deve acessar diretamente o SQLite ou utilizar credenciais da Shopee.

### Provedores

Utilize a arquitetura de provedores para permitir a substituição da fonte de dados.

Considere:

- `ShopeeProvider`: integração oficial.
- `DemoProvider`: dados fictícios.
- `CsvProvider`: importação de relatórios.

Mantenha os contratos dos provedores consistentes.

A troca de provedor não deve exigir reescrever os módulos que consomem seus dados.

Não misture dados reais e fictícios sem identificação explícita.

---

## 6. DESIGN E INTERFACE

O arquivo `DESIGN.md` é a autoridade visual do projeto.

**Leia-o integralmente antes de criar ou modificar qualquer interface.**

Não invente uma nova identidade visual.

Não introduza cores, componentes ou padrões visuais incompatíveis com o documento.

Respeite especialmente:

- Paleta monocromática com azul-diamante como único acento.
- Syne para títulos, marca e números de destaque.
- Inter para textos, formulários e tabelas.
- Espaçamento generoso.
- Sidebar fixa em desktop.
- Métricas em faixas horizontais.
- Tabelas como padrão de apresentação de dados.
- Cards somente quando houver justificativa.
- Estados vazios bem construídos.
- Acessibilidade e navegação por teclado.
- Animações discretas e funcionais.

### Ícones

Utilize exclusivamente Lucide para os ícones da interface.

É obrigatório salvar os SVGs utilizados em:

`frontend/src/assets/icons/`

Não utilizar emojis como substitutos de ícones.

Não utilizar ícones carregados de CDNs.

Centralize e padronize o uso dos ícones para evitar duplicações e inconsistências.

### Qualidade visual

Não considere uma tela concluída apenas porque está funcional.

Verifique:

- Hierarquia visual.
- Alinhamentos.
- Espaçamentos.
- Tipografia.
- Responsividade.
- Estados vazios.
- Estados de erro.
- Estados de carregamento.
- Foco e acessibilidade.

Antes de entregar, execute o checklist do `DESIGN.md`.

Evite padrões genéricos de interface e elementos decorativos sem finalidade.

---

## 7. SEGURANÇA E INTEGRAÇÕES

### Credenciais

- Credenciais devem permanecer no backend.
- Utilize variáveis de ambiente.
- Nunca exponha secrets ou tokens ao React.
- Nunca registre credenciais em logs.
- Nunca armazene credenciais nas memories.
- Mantenha `.env` no `.gitignore`.
- Utilize `.env.example` somente com nomes de variáveis e valores fictícios ou vazios.

### API da Shopee

Priorize exclusivamente a API oficial de afiliados.

Não invente endpoints, campos GraphQL, parâmetros, fórmulas de assinatura ou permissões.

Antes de implementar uma integração:

1. Consulte a documentação disponível.
2. Confirme os requisitos de autenticação.
3. Verifique os parâmetros aceitos.
4. Verifique os limites de requisições.
5. Identifique limitações de acesso da conta.

Não implemente scraping ou endpoints privados sem minha autorização explícita e análise prévia dos riscos.

Não tente contornar rate limits.

### Resiliência

Utilize:

- Timeouts.
- Retry controlado.
- Backoff exponencial.
- Tratamento de erros.
- Cache quando apropriado.
- Logs técnicos sem informações sensíveis.

Não repita automaticamente operações que possam gerar efeitos duplicados sem verificar sua segurança.

### Execução local

A aplicação deve operar em localhost.

Não exponha serviços desnecessariamente à rede local ou à internet.

Mantenha as configurações de CORS restritas às origens necessárias.

---

## 8. BANCO DE DADOS

SQLite é a fonte persistente dos dados da aplicação.

Não utilize LocalStorage como substituto do banco de dados.

Utilize:

- SQLAlchemy 2.
- Relacionamentos e chaves estrangeiras.
- Restrições de integridade.
- Índices quando houver justificativa.
- Transações para operações relacionadas.
- Migrations para alterações estruturais.

### Regras importantes

- Não apagar dados existentes para facilitar testes.
- Não recriar o banco automaticamente quando já existir.
- Não utilizar alterações destrutivas de schema sem autorização.
- Preservar histórico de links.
- Evitar registros duplicados.
- Manter relacionamentos consistentes entre produtos, links, lotes e listas.

Antes de alterar o modelo de dados, avalie o impacto nas funcionalidades existentes.

Registre decisões estruturais importantes em `docs/architecture/`.

---

## 9. TESTES E VALIDAÇÃO

Toda funcionalidade relevante deve ser acompanhada de testes.

### Backend

Utilize Pytest para verificar:

- Regras de negócio.
- Validações.
- Persistência.
- Integridade do banco.
- Tratamento de erros.
- Provedores.
- Duplicidades.

### Frontend

Utilize Vitest para verificar:

- Componentes.
- Hooks.
- Formulários.
- Regras de apresentação.
- Estados e transformações de dados.

### E2E

Utilize Playwright para verificar os fluxos completos da aplicação.

Não escreva testes que apenas verifiquem a presença de elementos quando for possível validar o comportamento real.

Os testes devem verificar os resultados das operações.

### Regras de validação

- Execute os testes relacionados à alteração.
- Corrija regressões introduzidas.
- Verifique os logs e erros do console.
- Não declare testes aprovados sem executá-los.
- Informe testes que não foram executados e seus motivos.

Não esconda erros para fazer os testes passarem.

---

## 10. MEMORIES E APRENDIZADO CONTÍNUO

Utilize a estrutura existente:

- `memories/Results/`
- `memories/Patterns/`
- `memories/gotchas/`
- `memories/INDEX.md`

### Results

Registre entregas importantes, resultados comprovados e decisões concluídas.

### Patterns

Registre padrões reutilizáveis e soluções arquiteturais comprovadas.

### gotchas

Registre erros relevantes, suas causas, limitações descobertas e formas de evitá-los.

### Regras

- Consulte memories relevantes antes de implementar.
- Não repita erros já documentados.
- Não registre suposições como fatos.
- Não crie registros duplicados.
- Atualize o INDEX.md quando adicionar um registro.
- Escreva de maneira objetiva, explicando o contexto e a solução.

Memories complementam a documentação oficial. Elas não substituem o código, os testes ou as decisões arquiteturais vigentes.

---

## 11. ORGANIZAÇÃO DO DESENVOLVIMENTO

Respeite rigorosamente as fases definidas no prompt de desenvolvimento e nas decisões aprovadas.

### Fase 1

MVP:

- Estrutura do projeto.
- Configuração.
- Banco de dados.
- Provedores.
- Busca de produtos.
- Geração de links em lote.
- Sub IDs.
- Histórico.

### Fase 2

- Conversion Report.
- Dashboard.
- Gráficos.
- Metas.
- Importação CSV.

### Fase 3

- Vídeos.
- Associação entre produtos e vídeos.
- Templates.
- Instagram.
- WhatsApp.

Não antecipar funcionalidades de fases futuras sem autorização.

Divida implementações grandes em etapas pequenas.

Não considere uma fase concluída até que seus critérios de aceitação tenham sido verificados.

---

## 12. COMUNICAÇÃO E ENTREGA

Trabalhe como um engenheiro explicando decisões a um desenvolvedor iniciante/intermediário.

Seja direto e técnico, mas explique conceitos importantes em linguagem simples.

Ao concluir uma tarefa relevante, apresente:

1. O que foi realizado.
2. Arquivos criados ou modificados.
3. Decisões técnicas importantes.
4. Testes executados.
5. Resultado dos testes.
6. Limitações conhecidas.
7. Próxima etapa recomendada.

Não afirme que algo está funcionando sem evidências.

Não esconda limitações ou erros.

Não faça commits automaticamente.

Não modifique branches ou histórico Git sem autorização.

Não execute comandos destrutivos sem autorização.

Quando concluir uma etapa, sugira uma mensagem de commit em português.

---

## 13. PRINCÍPIO GERAL

Antes de implementar qualquer coisa, compreenda o contexto.

Antes de adicionar complexidade, verifique se ela é necessária.

Antes de refatorar, entenda o que já existe.

Antes de considerar uma funcionalidade pronta, teste seu comportamento.

**Construa o Gnzl Achados com consistência, sem pressa para adicionar funcionalidades e sem comprometer a qualidade da fundação técnica.**