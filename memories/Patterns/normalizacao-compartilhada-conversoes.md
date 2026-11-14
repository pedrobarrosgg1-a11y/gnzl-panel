# Normalização compartilhada entre origens de conversão

Data: 2026-11-13

## Contexto

Pedidos chegam por CSV e pela Open API da Shopee, mas caem na mesma tabela
`orders` e alimentam o mesmo dashboard. Se cada importador normalizasse do seu
jeito, o mesmo pedido poderia virar dois grupos de status diferentes, dois Sub
IDs diferentes e números diferentes no relatório.

## Padrão

Separar em três camadas:

1. **Validação da fonte** — cada importador valida o que é específico do seu
   formato (colunas do CSV, resposta GraphQL). Erros apontam linha/campo.
2. **Normalização comum** — `app/core/conversion_rules.py` é a única
   implementação de status, Sub IDs, canal, cortes, quantidade padrão e valores
   não negativos. Nenhuma origem reimplementa.
3. **Persistência** — os dois caminhos gravam os mesmos campos já
   normalizados; o `raw_data` preserva o original para auditoria.

Primitivas puramente textuais ficam em `app/core/normalization.py`, para que
`core` não dependa de `services`.

## Como garantir que continua igual

Um teste de equivalência percorre os dois caminhos com o mesmo pedido
(`backend/tests/services/test_conversion_normalization.py`) e compara campo a
campo. Uma regra alterada em um lado só quebra o teste, não o relatório.

## Quando usar

Sempre que duas fontes alimentarem a mesma entidade agregada: importação CSV,
API oficial, dados demo. Vale também para metas futuras, que vão ler as mesmas
métricas.
