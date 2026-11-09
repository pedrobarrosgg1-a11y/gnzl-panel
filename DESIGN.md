# DESIGN.md — Gnzl Achados

Guia de design para qualquer pessoa ou IA que for construir ou alterar a interface do Gnzl Achados (painel pessoal de afiliado Shopee, com buscas automatizadas). Leia inteiro antes de escrever UI. Em caso de dúvida, escolha a opção com menos elementos.

Arquivos de apoio: `gnzl-design-system.css` (tokens e componentes) e o artefato de design com logotipo, emblema, favicon, posts e a proposta do dashboard.

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
