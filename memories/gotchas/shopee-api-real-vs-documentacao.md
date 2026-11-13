# API real da Shopee difere da documentação não oficial

Data: 2026-11-12

## Contexto

A documentação comunitária em `affiliateshopee.com.br/documentacao` foi usada
como ponto de partida, mas a introspecção GraphQL e as respostas reais mostraram
divergências que quebrariam o código se fossem seguidas literalmente.

## Divergências confirmadas

| Ponto | Documentação | API real |
|---|---|---|
| input do link | `GenerateShortLinkInput` | `ShortLinkInput` |
| status no relatório | `orderStatus` no nó | `conversionStatus` |
| domínio do link curto | `shope.ee` | `s.shopee.com.br` |
| `listType: 0` | recomendado | retorna `10000` em busca por keyword |
| filtro de preço/comissão | não documentado | não existe em `productOfferV2` |
| query de cliques | não citada | não existe |

## Sintomas

- `10010`: `Unknown type "GenerateShortLinkInput"`.
- `10010`: `Cannot query field "orderStatus" on type "ConversionReport"`.
- `10000`: `System Error` intermitente. Não é exclusivo de `listType: 0` nem de
  muitas chamadas: em 20 chamadas válidas e idênticas (`listType: 1`, página 2),
  11 funcionaram. As falhas voltam em menos de 1 s; as respostas boas levam
  cerca de 5 s. Uma sequência de retries pode atravessar uma janela ruim.

## Solução

- Introspecção GraphQL como fonte da verdade para nomes de tipos e campos.
- `listType: 1` sempre explícito.
- `ShortLinkInput` na mutation.
- `conversionStatus` no relatório.
- `10000` com até 8 tentativas em queries e backoff de 0,5 s a 2 s.
- `10030`/HTTP 429 com no máximo 3 tentativas, para respeitar o rate limit.
- Mutations sem retry: uma resposta perdida pode significar link já criado.

## Lição

Documentação não oficial serve para orientar a exploração, não para definir o
contrato. Antes de implementar, confirmar tipos e campos com introspecção ou
com uma resposta real. Não fixar domínio de link, total de resultados nem
catálogo de categorias que a API não fornece.
