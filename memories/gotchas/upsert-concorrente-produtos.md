# Upsert de produtos precisa ser atômico

Data: 2026-11-12

## Sintoma

No primeiro acesso a um banco vazio, a busca de produtos podia responder 500
com `Erro interno`. O log mostrava:

```text
sqlite3.IntegrityError: UNIQUE constraint failed:
products.item_id, products.shop_id, products.data_source
```

## Causa

O repositório fazia `SELECT` dos produtos existentes, criava os ausentes e só
então executava `flush()`. Duas requisições simultâneas — o React em modo
estrito dispara o efeito de busca duas vezes no desenvolvimento — enxergavam o
mesmo produto como inexistente e ambas tentavam inserir.

Verificar antes de inserir não é atômico. O índice único estava correto; a
gravação é que precisava resolver a corrida.

## Solução

Em `backend/app/repositories/products.py`, usar o upsert nativo do SQLite:

```python
statement = sqlite_insert(Product).values(values)
statement = statement.on_conflict_do_update(
    index_elements=["item_id", "shop_id", "data_source"],
    set_={...},
)
session.execute(statement)
```

Depois do `INSERT ... ON CONFLICT`, os produtos são relidos por identidade e
devolvidos na mesma ordem da entrada. O teste
`backend/tests/services/test_products_repository.py` usa duas threads com
barreira para reproduzir a concorrência e confirmar que sobra uma única linha.

## Lição

"Upsert" implementado como consulta seguida de inserção não é idempotente sob
concorrência. A garantia deve vir da restrição única mais uma operação atômica
do banco. O modo estrito do React é útil justamente por expor esse tipo de
corrida no backend durante o desenvolvimento.
