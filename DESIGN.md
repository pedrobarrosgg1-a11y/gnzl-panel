# DESIGN.md — Gnzl Achados

## Parte 1 — Base (original)

Guia de design para qualquer pessoa ou IA que for construir ou alterar a interface do Gnzl Achados (painel pessoal de afiliado Shopee, com buscas automatizadas). Leia inteiro antes de escrever UI. Em caso de dúvida, escolha a opção com menos elementos.

Arquivos de apoio: `gnzl-design-system.css` (tokens e componentes) e o artefato de design com logotipo, emblema, favicon, posts e a proposta do dashboard.

> **Estrutura deste arquivo.** A **Parte 1** (abaixo) é o DESIGN.md original, preservado sem alterações. A **Parte 2**, no final, é o adendo da versão 2 (paleta funcional, modo escuro e dashboard rico). Em caso de conflito no produto (site e painel), vale a Parte 2. Para marca e material de divulgação, valem as duas, com a Parte 1 como base.

---

## 1. Essência

- **Estética:** minimalismo moderno, monocromático, com um único acento. Silencioso, preciso, com muito espaço.
- **Personalidade:** direto, confiante, sem enfeite. A marca é a tipografia, não uma ilustração.
- **Metáfora:** radar. Uma busca que pinga e encontra. O "ping" (ponto com anel) é a assinatura visual.
- **Regra de ouro:** cada elemento precisa ter um propósito. Se não tem, remova.

## 2. Marca

- **Nome:** `gnzl` (sempre minúsculo no logotipo) + `achados` pequeno e espaçado embaixo.
- **Logotipo:** palavra "gnzl" em Syne 800, letras coladas (-5 px em 104 px), seguida do ping. "achados" em Syne 500, espaçamento de 11 a 13 px.
- **Emblema:** disco preto, fio fino azul-diamante, "g" branco em Syne 800 e ping.
- **Favicon:** quadrado preto com cantos arredondados (22%), "g" branco e ping azul-diamante, sem o fio externo (some em tamanho pequeno).
- **Versões do logotipo:** fundo branco (texto preto, ping preto), fundo preto (texto branco, ping azul-diamante), fundo azul-diamante (texto preto, ping preto).
- Nunca usar diamante/joia como símbolo. Nunca esticar, girar ou aplicar efeito.

## 3. Cores

Use somente estas. Sem gradientes.

| Token | Valor | Uso |
|---|---|---|
| `--gz-black` | `#0A0A0A` | Texto principal, botão primário, fundos escuros |
| `--gz-white` | `#FFFFFF` | Fundo principal, texto sobre escuro |
| `--gz-blue` | `#B9F2FF` | **Único acento.** Destaques, foco, ping sobre escuro, banners |
| `--gz-blue-ink` | `#0A6E9A` | Texto e links de acento **sobre fundo claro** (contraste 5,7:1) |
| `--gz-gray-700` | `#3A3A3A` | Texto secundário, divisores sobre escuro |
| `--gz-gray-500` | `#737373` | Rótulos, textos de apoio, placeholders |
| `--gz-gray-200` | `#E6E6E6` | Bordas e divisores sobre claro |
| `--gz-gray-100` | `#F5F5F5` | Superfícies discretas, placeholders de imagem |

Regras:
- O azul-diamante `#B9F2FF` **nunca** é texto sobre branco. Sobre branco, use `--gz-blue-ink` ou preto.
- No máximo **uma cor de acento por tela**.
- Texto sobre azul-diamante é sempre preto.
- Contraste mínimo de texto: 4,5:1 (3:1 para texto grande a partir de 24 px).

### Estados semânticos (proposta, ainda não definida no design)
O design atual não define cor de erro ou sucesso. Até decidir, comunique estado por **texto + ícone/ping + peso**, não só por cor. Se for necessário um vermelho funcional para erros destrutivos, aprove um único tom antes de usar e restrinja a mensagens de erro.

## 4. Tipografia

| Papel | Fonte | Peso | Notas |
|---|---|---|---|
| Display (marca, títulos de página, números grandes) | **Syne** | 800 | minúscula, `letter-spacing: -0.04em`, `line-height: 0.95` |
| Rótulo | **Syne** | 500 | minúscula, `letter-spacing: 0.3em`, 11 a 15 px |
| Corpo, tabelas, formulários | **Inter** | 400 / 500 | `line-height` 1,5 |

> Nota: fontes neutras de uso comum são vistas como sinal de interface genérica quando são a única fonte. Aqui a Syne carrega a identidade e a Inter fica restrita a corpo e dados. Pode ser trocada por outra fonte neutra mais distinta, desde que mantenha a legibilidade em tamanhos pequenos.

Escala de referência:

| Uso | Tamanho |
|---|---|
| Hero / pergunta principal | 54 px (display) |
| Título de página | 34 px (display) |
| Números de métrica | 44 a 46 px (display) |
| Título de seção/estado vazio | 30 px (display) |
| Corpo | 16 px / 24 px |
| Texto de apoio | 13 a 15 px |
| Rótulo | 11 a 12 px (Syne 500, tracking 0,3em) |

Mantenha contraste forte entre tamanhos (passo mínimo de 1,25x). Evite mais de 3 níveis de tamanho numa mesma região.

Não use a Syne em texto corrido nem em tamanhos abaixo de 11 px. Hospede as fontes localmente (o sistema roda local) em vez de depender de CDN.

## 5. Espaçamento, bordas e raios

- **Escala:** 4, 8, 12, 16, 24, 32, 48, 64 px (`--gz-s1` a `--gz-s16`). Use múltiplos de 4.
- **Bordas:** 1,5 px, cor `--gz-gray-200` sobre claro e `--gz-gray-700` sobre escuro.
- **Raios:** 8 (pequeno), 14 (campos), 22 (cards e banners), pílula (botões, selos).
- **Sombras:** não usar. Separação por espaço, borda fina ou contraste de fundo.
- Respiro generoso. Em caso de dúvida, aumente o espaço antes de adicionar um divisor.

## 6. Assinatura: o ping

Ponto sólido com anel concêntrico fino (`.gz-ping`). Usos permitidos:

1. Indicador de status (buscando, pausado, novo achado).
2. Item ativo na navegação.
3. Final do logotipo.
4. Ilustração de estado vazio: anéis concêntricos com opacidade decrescente e um ponto central.

Não usar o ping como enfeite aleatório nem animar sem função. Animação, se houver, é um pulso lento e discreto apenas durante uma busca em andamento, e deve respeitar `prefers-reduced-motion`.

## 7. Layout e navegação

- **Estrutura:** barra lateral fixa (cerca de 248 px) + área principal com cabeçalho de página.
- **Barra lateral:** marca no topo; itens como texto, sem ícone em caixa; item ativo com ping e peso 500; seção "em breve" discreta (cinza, com a fase à direita em texto simples, sem selo colorido); rodapé com estado do sistema (ex.: modo demo e versão).
- **Cabeçalho:** título da página em display à esquerda; filtro de período e indicadores de estado à direita; borda inferior fina.
- **Página:** uma ação principal por tela, com o maior peso visual e na posição mais alta.
- **Colunas:** no máximo duas por região. Evite colunas de alturas desiguais lado a lado.
- **Responsivo:** a barra lateral vira menu recolhível em telas estreitas; alvos de toque de pelo menos 44 px.

## 8. Componentes

Classes de referência em `gnzl-design-system.css`.

### Botões (`.gz-btn`)
- **Primário:** fundo preto, texto branco, pílula, 44 px de altura. Um por região.
- **Destaque (`--accent`):** fundo azul-diamante, texto preto. Para uso sobre fundo escuro.
- **Contorno (`--outline`):** transparente, borda da cor do texto.
- **Fantasma (`--ghost`):** só texto.
- Foco visível: anel de 3 px em azul-diamante com 2 px de afastamento. Hover discreto (opacidade).

### Campo (`.gz-input`)
44 px de altura, raio 14, borda cinza 200; no foco, borda preta. Para a busca principal, versão pílula de 56 px com ícone de lupa de traço fino.

### Selo / status (`.gz-badge` + `.gz-ping`)
Pílula com borda da cor do texto, 28 px. Estados: `buscando`, `pausado`, `novo achado`. Sempre com texto, nunca só cor.

### Card (`.gz-card`)
Use **apenas** quando o item for uma unidade clicável ou comparável, como um produto. Nunca para métrica, atalho ou dado tabular. Nunca card dentro de card.

### Métricas
Faixa horizontal com divisores finos entre os itens (rótulo cinza pequeno + número em display). Sem caixas, sem ícone em bloco.

### Atalhos e listas de ações
Linhas separadas por divisor fino, com título, descrição curta e seta. Sem cards.

### Tabelas
Padrão para dados (pedidos, histórico de links, produtos). Cabeçalho em rótulo cinza, linhas com divisor fino, números alinhados à direita, ordenação clara, filtros acima. Sem zebra pesada.

### Estado vazio
Obrigatório em toda área que pode ficar sem dados. Estrutura: ilustração em anéis (ping), título curto em display, 1 a 2 linhas explicando o que aparecerá ali, e **um botão** com a próxima ação. Não mostrar gráfico vazio nem zeros espalhados.

### Banner (`.gz-banner`)
Variações `--dark`, `--blue`, `--light`. Título em display, rótulo pequeno em Syne 500, um CTA. Anéis de radar como decoração opcional, sem competir com o texto.

## 9. Estados da interface

- **Carregando:** indicador discreto (ping pulsando) e texto curto. Evite esqueletos pesados.
- **Vazio:** ver "Estado vazio".
- **Erro:** mensagem em linguagem simples, dizendo o que houve e o que fazer. Para falhas da API da Shopee, explicar o acesso e oferecer alternativa (ex.: importar CSV).
- **Sucesso:** confirmação breve e discreta (ex.: "link copiado"), sem modal.
- **Desabilitado:** cinza 500, sem sombra, com `cursor: not-allowed`.
- **Modo demo:** sempre sinalizado no cabeçalho e na barra lateral.

## 10. Movimento

Mínimo e funcional: transições de 120 a 200 ms em hover e foco. Sem parallax, sem animações de entrada decorativas. Respeitar `prefers-reduced-motion`.

## 11. Acessibilidade

- Contraste de texto de pelo menos 4,5:1.
- Foco visível em todo elemento interativo.
- Estado nunca comunicado só por cor.
- Alvos de toque de pelo menos 44 px.
- Ícones decorativos com `aria-hidden`; ícones com função com rótulo.
- Navegação completa por teclado.

## 12. Conteúdo e tom de voz

- Português do Brasil, direto e específico. Diga o que o sistema faz, em verbos e substantivos concretos.
- Títulos e rótulos em minúsculas (identidade da marca). Corpo em frase normal.
- Evite frases genéricas de SaaS (ex.: "turbine", "potencialize", "soluções completas") e saudações vazias ("bem-vindo ao painel").
- Prefira uma pergunta ou ação ao invés de boas-vindas (ex.: "o que vamos achar hoje?").
- Números de moeda no formato `R$ 0,00`.

## 13. Anti-slop (proibido)

Estes padrões fazem a interface parecer gerada por IA e genérica:

- Grade de cards iguais com ícone + título + texto repetidos.
- Ícone em bloco colorido acima do título.
- Card dentro de card; tudo embrulhado em card.
- Hero centralizado com dois CTAs competindo.
- Gradientes (inclusive em texto), roxo/índigo, glassmorphism, brilho neon.
- Sombras suaves em todos os elementos.
- Várias cores de destaque ao mesmo tempo.
- Emojis como ícones.
- Selos pulsando sem função.
- Cantos exageradamente redondos em tudo.
- Hierarquia plana (tamanhos de fonte muito próximos).
- Zeros e gráficos vazios no lugar de um estado vazio útil.

## 14. Material de divulgação (posts e banners)

- **Formato de post:** 1080 x 1350 (4:5), carrossel.
- **Capa:** fundo preto, anéis de radar no canto, título em Syne 800 branco com a frase de destaque em azul-diamante, marca "gnzl" + ping no rodapé.
- **Posts de produtos (9, 6 e 3):** fundo branco, cards cinza-claro com selo numérico preto no canto, código em pílula preta com "cód" em azul-diamante (modelos de 9 e 6 produtos); modelo de 3 com números grandes alternando de lado.
- **Post final:** fundo preto, passo a passo de como usar o código na busca da Shopee, chamada para pedir o link nos comentários e, na versão estendida, chamada para o grupo de promoções e achados no WhatsApp (link na bio).

## 15. Checklist antes de entregar

- [ ] Só as cores desta lista; apenas um acento por tela.
- [ ] Syne só em títulos, rótulos e números; Inter no resto.
- [ ] Nenhum gradiente, sombra forte ou card desnecessário.
- [ ] Existe uma ação principal clara na tela.
- [ ] Métricas em faixa, atalhos em lista, dados em tabela.
- [ ] Todo estado vazio tem explicação e um botão.
- [ ] Contraste, foco e alvos de toque verificados.
- [ ] Fontes hospedadas localmente.
- [ ] Rodada final de subtração feita: tudo que não tem propósito foi removido.

## 16. Tokens de referência

```css
:root {
  /* cores */
  --gz-black: #0A0A0A;
  --gz-white: #FFFFFF;
  --gz-blue: #B9F2FF;
  --gz-blue-ink: #0A6E9A;
  --gz-gray-700: #3A3A3A;
  --gz-gray-500: #737373;
  --gz-gray-200: #E6E6E6;
  --gz-gray-100: #F5F5F5;

  /* tipografia */
  --gz-font-display: 'Syne', Arial, sans-serif;
  --gz-font-body: 'Inter', Arial, sans-serif;

  /* raios */
  --gz-r-sm: 8px;
  --gz-r-md: 14px;
  --gz-r-lg: 22px;
  --gz-r-pill: 999px;

  /* espaçamento */
  --gz-s1: 4px;  --gz-s2: 8px;  --gz-s3: 12px; --gz-s4: 16px;
  --gz-s6: 24px; --gz-s8: 32px; --gz-s12: 48px; --gz-s16: 64px;
}
```

---

# Parte 2 — Adendo v2 (visual atual do site)

Guia de design para quem for construir ou alterar a interface do Gnzl Achados, um painel pessoal de afiliado Shopee com buscas automatizadas, com foco em moda. Leia inteiro antes de escrever UI. Em caso de dúvida, escolha a opção com menos elementos e use cor só quando ela significar algo.

**O que mudou na v2:** paleta ampliada com cores funcionais (menta, âmbar, coral), modo escuro completo, mais detalhes de interface (ícones, gráficos, mini tendências, selos de status, meta do mês) e regras novas sobre painéis. A v1 pedia um único acento. Agora o azul-diamante é a cor da marca e as demais cores existem apenas para informar.

Arquivos de apoio: `gnzl-design-system.css` (tokens e componentes) e o artefato de design com logotipo, emblema, favicon, fotos de perfil, posts e as pranchas "Dashboard v2 — claro" e "Dashboard v2 — escuro", que são a referência visual do site.

**Precedência:** no site e no painel, onde a Parte 1 e esta Parte 2 divergirem, vale esta Parte 2. As diferenças principais são: acento único (Parte 1, seção 3) passa a ser azul-diamante de marca mais cores funcionais com função; "nunca card" passa a permitir painéis só para dados que precisam de moldura; tema único passa a ter claro e escuro. Todo o resto da Parte 1 (marca, tipografia, ping, anti-slop, material de divulgação) continua valendo.

---

## 2.1. Essência

- **Estética:** minimalismo moderno com personalidade. Base neutra, azul-diamante como assinatura e cores de apoio funcionais.
- **Personalidade:** direto, confiante, com humor leve. A marca é a tipografia, não uma ilustração.
- **Metáfora:** radar. O "ping" (ponto com anel) é a assinatura visual da interface.
- **Regra de ouro:** cada elemento e cada cor precisa ter um propósito. Se não tem, remova.
- **Equilíbrio:** a v2 tem mais densidade de informação que a v1, mas continua respirando. Mais detalhe vem de dados, ícones finos, gráficos e status, nunca de caixas, sombras ou decoração.

## 2.2. Marca

- **Nome:** `gnzl` (minúsculo) + `achados` pequeno e espaçado embaixo.
- **Logotipo:** "gnzl" em Syne 800, letras coladas, seguido do ping. "achados" em Syne 500 com espaçamento largo.
- **Emblema, favicon e foto de perfil:** "g" em Syne 800 sobre preto ou azul-diamante, com o ping ou outro detalhe aprovado (etiqueta, marca-texto, corte, cabide, zíper). Para foto de perfil, evite repetir círculos e ondas de radar.
- **No site:** o ping pode aparecer ao lado da marca na barra lateral (em menta, indicando sistema ativo) e como indicador de status. Nunca como decoração solta.
- Nunca usar diamante/joia como símbolo. Nunca esticar, girar ou aplicar efeito na marca.

## 2.3. Cores

### 2.3.1 Marca e neutros (base)

| Token | Valor | Uso |
|---|---|---|
| `--gz-black` | `#0A0A0A` | Texto no claro, fundo no escuro, botão primário no claro |
| `--gz-white` | `#FFFFFF` | Superfície no claro, texto no escuro |
| `--gz-blue` | `#B9F2FF` | **Cor da marca.** Item ativo do menu, botão primário no escuro, card de meta, destaques |
| `--gz-blue-ink` | `#0A6E9A` | Texto, links e linhas de gráfico de marca **sobre fundo claro** |

### 2.3.2 Cores funcionais (novas na v2)

Usadas só para informar: status, variação de números, séries de gráfico e pequenos indicadores. Nunca como fundo de bloco grande, nunca como enfeite.

| Papel | Claro (fundo / texto) | Escuro (fundo / texto) | Significa |
|---|---|---|---|
| Menta | `#DDF8EE` / `#0B7A55` | `#0F2E25` / `#2BD9A0` | sucesso, concluído, crescimento, sistema ativo |
| Âmbar | `#FFF1CC` / `#8A5B00` | `#33280A` / `#FFC24B` | pendente, aviso, modo demo |
| Coral | `#FFE1E1` / `#B42318` | `#341515` / `#FF7A7A` | cancelado, erro, queda |

Séries de gráfico (nesta ordem): série 1 = azul (`#0A6E9A` no claro, `#B9F2FF` no escuro), série 2 = menta (`#0E9F6E` no claro, `#2BD9A0` no escuro), série 3 = âmbar (`#E0A100` no claro, `#FFC24B` no escuro).

### 2.3.3 Regras de cor

- O azul-diamante `#B9F2FF` **nunca** é texto sobre fundo claro. Use `--gz-blue-ink` ou preto.
- Texto sobre azul-diamante é sempre preto.
- Máximo de **três cores funcionais por tela**, além do azul de marca e dos neutros.
- Cor nunca é a única forma de comunicar estado: sempre acompanha texto (ex.: selo "concluído") ou ícone.
- Sem gradientes. Sem roxo/índigo. Sem neon.
- Contraste de texto de pelo menos 4,5:1 (3:1 para texto grande a partir de 24 px). Verifique cada par fundo/texto da tabela acima com uma ferramenta de contraste antes de publicar.

### 2.3.4 Tokens semânticos (use estes no código, não os valores diretos)

| Token | Claro | Escuro |
|---|---|---|
| `--gz-bg` (fundo da página) | `#F6F8F9` | `#0A0A0A` |
| `--gz-sidebar` | `#FFFFFF` | `#0F0F0F` |
| `--gz-surface` (painéis) | `#FFFFFF` | `#141414` |
| `--gz-border` | `#E3E8EB` | `#262626` |
| `--gz-text` | `#0A0A0A` | `#FFFFFF` |
| `--gz-muted` | `#6B7378` | `#9AA3A8` |
| `--gz-track` (trilho de barra) | `#EAEFF1` | `#262626` |
| `--gz-thumb` (placeholder de imagem) | `#E8F6FB` | `#1D2A30` |
| `--gz-btn-bg` / `--gz-btn-fg` | `#0A0A0A` / `#FFFFFF` | `#B9F2FF` / `#0A0A0A` |

## 2.4. Modo escuro

- **Disponibilidade:** claro e escuro desde o início. Respeitar `prefers-color-scheme` na primeira visita e permitir troca manual no rodapé da barra lateral (controle segmentado "claro / escuro"). Guardar a escolha no navegador e aplicá-la antes da pintura para evitar o piscar de tema.
- **Como pensar:** não é inverter cores. Defina os tokens semânticos da seção 2.3.4 e use só eles nos componentes.
- **Profundidade:** no escuro, hierarquia vem de superfícies mais claras sobre o fundo (`#0A0A0A` → `#0F0F0F` → `#141414`), com borda fina `#262626`. Sem sombras.
- **Botão primário:** azul-diamante com texto preto no escuro; preto com texto branco no claro.
- **Cores funcionais:** usar as variantes claras do escuro (tabela 2.3.2). Evitar fundos saturados grandes.
- **Imagens:** fotos de produto e de look continuam com seus fundos. Placeholders usam `--gz-thumb`. Não aplicar filtro de brilho.
- **Gráficos:** linhas na versão do escuro, grade em `--gz-border`, área sob a linha com 10% de opacidade.
- **Teste:** toda tela deve ser revisada nos dois modos antes de entregar.

## 2.5. Tipografia

| Papel | Fonte | Peso | Notas |
|---|---|---|---|
| Display (marca, títulos, números grandes) | **Syne** | 800 | minúscula, `letter-spacing: -0.04em`, `line-height: 0.95` |
| Rótulo | **Syne** | 500 | minúscula, `letter-spacing: 0.3em`, 11 a 15 px |
| Corpo, tabelas, formulários | **Inter** | 400 / 500 | `line-height` 1,5 |

Escala de referência:

| Uso | Tamanho |
|---|---|
| Pergunta principal da tela | 44 a 54 px (display) |
| Título de página | 34 a 36 px (display) |
| Número de métrica | 40 a 46 px (display) |
| Número secundário (comissão em tabela, projeção) | 18 a 26 px (display) |
| Corpo | 14 a 16 px |
| Texto de apoio e legendas | 12 a 13 px |
| Rótulo de seção | 11 a 12 px (Syne 500, tracking 0,3em) |

- A Syne nunca vai em texto corrido nem abaixo de 11 px.
- Hospede as fontes localmente (o sistema roda local). A Inter pode ser trocada por outra fonte neutra mais distinta, desde que continue legível em tamanho pequeno.
- Números em tabelas e métricas: alinhamento consistente e, se possível, algarismos tabulares.

## 2.6. Espaçamento, bordas e raios

- **Escala:** 4, 8, 12, 16, 24, 32, 48, 64 px. Múltiplos de 4.
- **Bordas:** 1,5 px na cor `--gz-border`.
- **Raios:** 8 (pequeno), 12 (item de menu), 14 (campos), 22 (painéis e blocos), pílula (botões, selos, filtros).
- **Sombras:** não usar. Separação por espaço, borda fina ou diferença de superfície.
- **Ritmo da página:** 22 a 24 px entre blocos, 40 px de margem lateral, 24 px de padding interno nos painéis.

## 2.7. Iconografia

- Ícones de traço fino: 20 px, `stroke-width` 1,8, pontas arredondadas, cor `currentColor`. Um único estilo em todo o sistema.
- Ícones só para navegação e ações. Nunca dentro de blocos coloridos acima de títulos (padrão genérico a evitar).
- Ícones decorativos com `aria-hidden`; ícones que funcionam como botão levam rótulo.
- Brilho de quatro pontas (sparkle): detalhe de destaque, usado no card da meta do mês e em material de divulgação. Uma vez por tela, no máximo.

## 2.8. Assinatura: o ping

Ponto sólido com anel concêntrico fino (`.gz-ping`). Usos permitidos:

1. Final do logotipo e ao lado da marca na barra lateral (menta = sistema ativo).
2. Indicador de status: sincronizado (menta), modo demo (âmbar), buscando.
3. Estado vazio: anéis concêntricos com opacidade decrescente.

Animação, se houver, é um pulso lento e só durante uma busca em andamento. Respeitar `prefers-reduced-motion`.

## 2.9. Layout e navegação

- **Estrutura:** barra lateral fixa de 248 px + área principal.
- **Barra lateral:**
  - Marca no topo (`gnzl` + ping menta).
  - Itens com ícone de traço fino e rótulo. **Item ativo:** pílula azul-diamante com texto preto.
  - Grupos: principais (Dashboard, Produtos, Gerar links, Histórico) e "em breve" (Metas, Importar CSV, Vídeos, Automação), em cor atenuada, com a fase em texto pequeno à direita e sem selo colorido.
  - Rodapé: estado do sistema (ping âmbar em modo demo e versão) e o seletor claro/escuro.
- **Cabeçalho da página:** título em display à esquerda. À direita: indicador de sincronização (ping menta + horário), controle de período segmentado e selo de modo demo.
- **Ordem do dashboard (de cima para baixo):**
  1. Pergunta principal + busca + atalhos de categoria.
  2. Faixa de métricas (sem caixas).
  3. Gráfico principal + card da meta do mês.
  4. Tabela de pedidos recentes + painéis menores (por rede, top produtos).
- **Uma ação principal por tela**, com o maior peso visual e na posição mais alta.
- **Responsivo:** barra lateral vira menu recolhível em telas estreitas; painéis empilham; alvos de toque de pelo menos 44 px.

## 2.10. Componentes

Classes de referência em `gnzl-design-system.css`.

### Botões (`.gz-btn`)
- **Primário:** pílula de 44 a 52 px. Usa `--gz-btn-bg` e `--gz-btn-fg` (preto no claro, azul-diamante no escuro). Um por região.
- **Contorno** e **fantasma:** secundários.
- Foco visível: anel de 3 px em azul-diamante (no claro, com 2 px de afastamento) para garantir contraste.

### Campo de busca
Pílula de 52 px, superfície `--gz-surface`, borda fina, ícone de lupa em traço. Ao lado, o botão primário e atalhos de categoria.

### Atalhos de categoria (chips de filtro)
Pílula de 34 px com borda fina e um pequeno ponto colorido da série (azul, menta, âmbar, alternando). Servem como filtro rápido (ex.: vestidos, tênis, bolsas). O ponto é decorativo funcional (agrupa) e não comunica estado.

### Controle segmentado
Para período (hoje, 7 dias, 30 dias) e tema (claro, escuro). Contêiner pílula com borda; opção ativa em `--gz-btn-bg`/`--gz-btn-fg` (ou azul-diamante, no caso do tema).

### Selo de status (`.gz-chip` / `.gz-badge`)
Pílula de 24 px com fundo e texto das cores funcionais (menta, âmbar, coral). Sempre com texto: "concluído", "pendente", "cancelado", "modo demo".

### Selo de variação
Mesmo selo, mostrando o delta de uma métrica: menta para alta (+12%), coral para queda (-0,3%).

### Faixa de métricas
Linha horizontal com divisores finos, sem caixas. Cada item: rótulo cinza, número em display, selo de variação e mini linha de tendência (96×32 px, `stroke-width` 2,5, cor da série). 4 a 5 itens.

### Painel (`.gz-panel`)
Superfície com borda de 1,5 px e raio de 22. **Só para dados que precisam de moldura**: gráfico, tabela, lista de barras, ranking. Título em rótulo cinza no topo. Nunca para métrica solta, atalho ou ação. Nunca painel dentro de painel.

### Card da meta do mês
Bloco de azul-diamante, texto preto: rótulo, valor atual e meta em display, barra de progresso (trilho preto a 14%, preenchimento preto), percentual, projeção do mês e quanto falta por dia. Um brilho de quatro pontas no canto. É o único bloco grande colorido da tela.

### Gráfico de linhas
- Máximo de 3 séries, nomeadas por legenda simples (ponto + rótulo).
- Grade horizontal em `--gz-border`, sem grade vertical, sem eixos pesados.
- Área sob a série principal com 10 a 12% de opacidade.
- Ponto final destacado com contorno na cor da superfície.
- Rótulos de dia em 12 px, cor atenuada. Sem 3D, sem pizza, sem donut. Para distribuição, usar barras.

### Lista de barras (distribuição)
Rótulo e percentual numa linha, barra de 10 px abaixo com trilho `--gz-track`. Cada categoria usa uma cor da série.

### Tabela de dados
Cabeçalho em 12 px atenuado; linhas de 56 px com divisor fino; selo de status; números de comissão em display pequeno; coluna de sub ID atenuada. Sem zebra. Link "ver todos →" no canto do painel, em `--gz-blue-ink` (ou azul-diamante no escuro).

### Lista de ranking (top produtos)
Linhas de 54 px com miniatura de 40 px (raio 12, `--gz-thumb`), nome, cliques e um selo menta com a comissão.

### Card de produto
Apenas quando o item for uma unidade clicável e comparável. Nunca para métrica ou atalho.

### Estado vazio
Obrigatório em toda área que pode ficar sem dados: ilustração em anéis, título curto em display, 1 a 2 linhas explicando o que aparecerá e **um botão** com a próxima ação. No modo demo, as telas mostram dados de exemplo, claramente sinalizados com o selo "modo demo · dados fictícios".

### Banner
Variações escura, azul-diamante e clara, para uso em páginas públicas e em comunicações. Mesma gramática: rótulo em Syne 500, título em display, um CTA.

## 2.11. Estados da interface

- **Carregando:** ping discreto e texto curto. Evite esqueleto pesado.
- **Vazio:** ver "Estado vazio".
- **Erro:** mensagem simples dizendo o que houve e o que fazer, em selo/linha coral com texto. Para falhas da API da Shopee, explique o acesso e ofereça alternativa (importar CSV).
- **Sucesso:** confirmação breve (ex.: "link copiado"), em menta, sem modal.
- **Desabilitado:** cor atenuada, `cursor: not-allowed`.
- **Sincronização:** sempre mostrar a data e hora da última sincronização, porque os dados da Shopee têm atraso.
- **Modo demo:** sinalizado no cabeçalho e no rodapé da barra lateral.

## 2.12. Movimento

Mínimo e funcional: transições de 120 a 200 ms em hover e foco; troca de tema sem animação longa. Sem parallax, sem entradas decorativas. Respeitar `prefers-reduced-motion`.

## 2.13. Acessibilidade

- Contraste de texto de pelo menos 4,5:1 nos dois temas.
- Foco visível em todo elemento interativo.
- Estado nunca só por cor.
- Gráficos com `aria-label` descrevendo o conteúdo e, quando possível, os dados também em tabela ou texto.
- Alvos de toque de pelo menos 44 px.
- Navegação completa por teclado, incluindo o seletor de tema.

## 2.14. Conteúdo e tom de voz

- Português do Brasil, direto e específico. Diga o que o sistema faz.
- Títulos e rótulos em minúsculas (identidade da marca). Corpo em frase normal.
- Evite frases genéricas de SaaS ("turbine", "potencialize") e saudações vazias ("bem-vindo ao painel").
- Prefira pergunta ou ação (ex.: "o que vamos achar hoje?").
- Moeda no formato `R$ 0,00`; percentuais com vírgula (`2,7%`).

## 2.15. Anti-slop (continua proibido)

- Grade de cards iguais com ícone + título + texto.
- Ícone em bloco colorido acima do título.
- Painel dentro de painel; tudo embrulhado em painel.
- Hero centralizado com dois CTAs competindo.
- Gradientes (inclusive em texto), roxo/índigo, glassmorphism, brilho neon.
- Sombras suaves em todos os elementos.
- Cor decorativa sem significado; mais de três cores funcionais por tela.
- Emojis como ícones.
- Selos pulsando sem função.
- Cantos exageradamente redondos em tudo.
- Hierarquia plana (tamanhos de fonte muito próximos).
- Gráfico decorativo sem dado real, e zeros espalhados no lugar de um estado vazio útil.

## 2.16. Material de divulgação (posts e banners)

O material de redes sociais mantém a paleta de marca (preto, branco e azul-diamante) e **não** usa as cores funcionais, que pertencem ao produto.

- **Formato de post:** 1080 x 1350 (4:5), carrossel.
- Capas com gancho (curiosidade, surpresa, identificação, comparação, antecipação, humor), versões de moda, posts de produtos (9, 6, 4, 3, 2 e 1 produto), top 5, mais clicados, kit temático, conferir antes de comprar, adivinha o preço, preço caiu, grupo do WhatsApp e encerramentos. Todos seguem as regras de marca desta seção e da seção 2.
- Sem pedido de comentário para receber o link: o caminho é o código no post, colado na busca da Shopee, mais o grupo do WhatsApp (link na bio).

## 2.17. Checklist antes de entregar

- [ ] Só tokens do sistema; nada de valor de cor solto no código.
- [ ] Funciona e foi revisado nos modos claro e escuro.
- [ ] Azul-diamante só em marca, item ativo, meta e botão primário do escuro.
- [ ] No máximo três cores funcionais; nenhuma sem significado.
- [ ] Syne só em títulos, rótulos e números; Inter no resto.
- [ ] Nenhum gradiente, sombra ou painel desnecessário.
- [ ] Existe uma ação principal clara na tela.
- [ ] Métricas em faixa, atalhos em lista, dados em painel ou tabela.
- [ ] Todo estado vazio tem explicação e um botão.
- [ ] Sincronização e modo demo sinalizados.
- [ ] Contraste, foco e alvos de toque verificados.
- [ ] Fontes hospedadas localmente.
- [ ] Rodada final de subtração: tudo sem propósito foi removido.

## 2.18. Tokens de referência

```css
:root,
[data-theme="light"] {
  /* marca */
  --gz-black: #0A0A0A;
  --gz-white: #FFFFFF;
  --gz-blue: #B9F2FF;
  --gz-blue-ink: #0A6E9A;

  /* semânticos (claro) */
  --gz-bg: #F6F8F9;
  --gz-sidebar: #FFFFFF;
  --gz-surface: #FFFFFF;
  --gz-border: #E3E8EB;
  --gz-text: #0A0A0A;
  --gz-muted: #6B7378;
  --gz-track: #EAEFF1;
  --gz-thumb: #E8F6FB;
  --gz-btn-bg: #0A0A0A;
  --gz-btn-fg: #FFFFFF;

  /* séries de gráfico */
  --gz-series-1: #0A6E9A;
  --gz-series-2: #0E9F6E;
  --gz-series-3: #E0A100;
  --gz-area: rgba(10, 110, 154, 0.12);

  /* status: fundo / texto */
  --gz-mint-bg: #DDF8EE;  --gz-mint-fg: #0B7A55;
  --gz-amber-bg: #FFF1CC; --gz-amber-fg: #8A5B00;
  --gz-coral-bg: #FFE1E1; --gz-coral-fg: #B42318;

  /* tipografia, raios, espaçamento */
  --gz-font-display: 'Syne', Arial, sans-serif;
  --gz-font-body: 'Inter', Arial, sans-serif;
  --gz-r-sm: 8px; --gz-r-md: 14px; --gz-r-lg: 22px; --gz-r-pill: 999px;
  --gz-s1: 4px; --gz-s2: 8px; --gz-s3: 12px; --gz-s4: 16px;
  --gz-s6: 24px; --gz-s8: 32px; --gz-s12: 48px; --gz-s16: 64px;
}

[data-theme="dark"] {
  --gz-bg: #0A0A0A;
  --gz-sidebar: #0F0F0F;
  --gz-surface: #141414;
  --gz-border: #262626;
  --gz-text: #FFFFFF;
  --gz-muted: #9AA3A8;
  --gz-track: #262626;
  --gz-thumb: #1D2A30;
  --gz-btn-bg: #B9F2FF;
  --gz-btn-fg: #0A0A0A;

  --gz-series-1: #B9F2FF;
  --gz-series-2: #2BD9A0;
  --gz-series-3: #FFC24B;
  --gz-area: rgba(185, 242, 255, 0.10);

  --gz-mint-bg: #0F2E25;  --gz-mint-fg: #2BD9A0;
  --gz-amber-bg: #33280A; --gz-amber-fg: #FFC24B;
  --gz-coral-bg: #341515; --gz-coral-fg: #FF7A7A;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --gz-bg: #0A0A0A;
    --gz-sidebar: #0F0F0F;
    --gz-surface: #141414;
    --gz-border: #262626;
    --gz-text: #FFFFFF;
    --gz-muted: #9AA3A8;
    --gz-track: #262626;
    --gz-thumb: #1D2A30;
    --gz-btn-bg: #B9F2FF;
    --gz-btn-fg: #0A0A0A;
    --gz-series-1: #B9F2FF;
    --gz-series-2: #2BD9A0;
    --gz-series-3: #FFC24B;
    --gz-area: rgba(185, 242, 255, 0.10);
    --gz-mint-bg: #0F2E25;  --gz-mint-fg: #2BD9A0;
    --gz-amber-bg: #33280A; --gz-amber-fg: #FFC24B;
    --gz-coral-bg: #341515; --gz-coral-fg: #FF7A7A;
  }
}
```

## 2.19. Histórico de versões

- **v2:** paleta funcional (menta, âmbar, coral), modo escuro, ícones de traço fino, gráficos, mini tendências, selos de status, card de meta, painéis para dados, regras de densidade, atualização da barra lateral e do cabeçalho.
- **v1:** estética monocromática com um único acento, dashboard com busca, faixa de métricas e estado vazio.
- **Estrutura do arquivo:** a Parte 1 (original) foi preservada integralmente e esta Parte 2 funciona como adendo.