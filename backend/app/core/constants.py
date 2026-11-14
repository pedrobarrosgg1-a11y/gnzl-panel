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

# Importação CSV: o arquivo é lido inteiro em memória. O teto evita que um
# upload acidental derrube o processo local.
MAX_IMPORT_BYTES = 10 * 1024 * 1024

# A Open API da Shopee só devolve conversões dos últimos 90 dias. O limite é
# aplicado no provedor e repetido no endpoint para a interface não oferecer uma
# janela que a fonte recusaria.
MAX_CONVERSION_WINDOW_DAYS = 90
