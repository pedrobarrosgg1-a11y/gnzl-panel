# SQLAlchemy: relationship nula sobrescreve a FK

## Sintoma

Uma linha de `imported_rows` era criada com `order_id` preenchido, mas era
gravada com `NULL` no banco.

## Causa

O objeto foi construído passando **os dois** vínculos:

```python
ImportedRow(order=None, order_id=existing_id)
```

Ao definir o relacionamento como `None`, o unit of work do SQLAlchemy
sincroniza a chave estrangeira com o valor do relacionamento no flush,
sobrescrevendo o `order_id` informado.

## Solução

Enviar apenas um dos dois. Quando só existe o id, não passe o relacionamento:

```python
values = {"order_id": existing_id}
# sem a chave "order"
ImportedRow(**values)
```

Quando o objeto de domínio já existe na sessão, prefira o relacionamento e
deixe o SQLAlchemy preencher a FK:

```python
ImportedRow(order=order)
```

## Onde isso apareceu

`backend/app/services/csv_import.py`, na criação das linhas de importação.
O teste de reimportação (`test_reimporting_the_same_file_skips_instead_of_duplicating`)
cobre o caso.
