"""Limites compartilhados entre modelos, serviços e schemas.

Ficam em um único lugar para o CHECK do banco e a validação da aplicação não
divergirem com o tempo.
"""

# Teto local enquanto o limite oficial da Shopee não for confirmado.
SUB_ID_MAX_LENGTH = 64
LIST_NAME_MAX_LENGTH = 120
PRODUCT_TITLE_MAX_LENGTH = 300
MAX_PAGE_SIZE = 100

# Teto por lote. Mantém a operação previsível e evita uma chamada externa
# descontrolada quando o provedor oficial for ativado.
MAX_BATCH_ITEMS = 200
