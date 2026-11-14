"""Regras de normalização compartilhadas por todas as origens de conversão.

CSV e Shopee gravam na mesma tabela ``orders``. Se cada importador tratasse
status, Sub IDs, canal e valores de um jeito, o dashboard somaria coisas
diferentes. Este módulo é a única implementação dessas regras: o importador CSV
e o provedor oficial apenas o consomem.

As regras aqui são de *normalização de dado já aceito*. Validação do arquivo
(campos obrigatórios, números inválidos) continua em cada importador, porque a
mensagem precisa apontar a linha e a coluna do relatório.
"""

import re

from app.core.constants import PRODUCT_TITLE_MAX_LENGTH, SUB_ID_MAX_LENGTH
from app.core.normalization import normalize_key

MAX_SUB_IDS = 5
MAX_STATUS_LENGTH = 60
MAX_CHANNEL_LENGTH = 80
MAX_ORDER_ID_LENGTH = 100
MAX_TITLE_LENGTH = PRODUCT_TITLE_MAX_LENGTH

# Toda linha de item representa pelo menos uma unidade. Quantidade ausente na
# fonte vira 1 nas duas origens; zero é um valor explícito, não um padrão.
DEFAULT_QUANTITY = 1

STATUS_GROUPS = ("pending", "approved", "cancelled", "refunded", "unknown")

_SUB_ID_SEPARATORS = re.compile(r"[,;|\s]+")

# Valores de dispositivo conhecidos. O canal é um código curto: normalizamos a
# caixa apenas quando o valor é um desses tokens, para que "app" do CSV e
# "APP" da Shopee sejam o mesmo canal sem transformar "Instagram" em
# "INSTAGRAM".
_DEVICE_CHANNELS = frozenset({"app", "web", "mobile", "desktop", "other"})

_EXACT_STATUS_GROUPS = {
    "all": "unknown",
    "unpaid": "pending",
    "pending": "pending",
    "completed": "approved",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "refunded": "refunded",
}

# Tokens em inglês e português, porque o CSV canônico pode trazer o texto do
# relatório traduzido e a API usa inglês. A ordem importa: cancelamento e
# reembolso vêm antes; pendência vem antes de aprovação para que "não pago" e
# "aguardando pagamento" não sejam lidos como pagos.
_CANCELLED_TOKENS = ("cancel",)
_REFUNDED_TOKENS = ("refund", "return", "devolu", "devolv", "reembols", "estorn")
_PENDING_TOKENS = (
    "unpaid",
    "nao pago",
    "não pago",
    "pending",
    "pend",
    "process",
    "ship",
    "enviad",
    "transit",
    "await",
    "aguard",
)
_APPROVED_TOKENS = (
    "complete",
    "conclu",
    "approv",
    "aprov",
    "paid",
    "pago",
    "deliver",
    "entreg",
    "faturad",
)


def status_group_from_raw(value: str | None) -> str:
    """Classifica o status bruto por tokens conhecidos.

    Não presume um vocabulário fechado: o relatório pode trazer texto em
    português, inglês ou um status novo. O valor bruto continua gravado em
    ``orders.status``; aqui só derivamos o grupo usado nas métricas.
    """
    token = (value or "").strip().casefold()
    if not token:
        return "unknown"

    exact = _EXACT_STATUS_GROUPS.get(token)
    if exact is not None:
        return exact
    if any(word in token for word in _CANCELLED_TOKENS):
        return "cancelled"
    if any(word in token for word in _REFUNDED_TOKENS):
        return "refunded"
    if any(word in token for word in _PENDING_TOKENS):
        return "pending"
    if any(word in token for word in _APPROVED_TOKENS):
        return "approved"
    return "unknown"


def split_sub_ids(value: str | None) -> tuple[str | None, ...]:
    """Separa um texto com vários Sub IDs em até cinco posições canônicas.

    Usado quando a fonte entrega os Sub IDs juntos (``utmContent`` da Shopee).
    A ordem é preservada e as posições que faltam viram ``None``.
    """
    if not value:
        return (None,) * MAX_SUB_IDS

    parts = _SUB_ID_SEPARATORS.split(value.strip())
    tokens = [
        token
        for token in (
            normalize_key(part, max_length=SUB_ID_MAX_LENGTH) for part in parts
        )
        if token
    ][:MAX_SUB_IDS]
    return tuple(tokens + [None] * (MAX_SUB_IDS - len(tokens)))


def normalize_channel(value: str | None) -> str | None:
    """Canal em formato curto e previsível.

    Espaços internos são colapsados e tokens de dispositivo conhecidos viram
    maiúsculas, para que ``app``, ``App`` e ``APP`` não virem três canais.
    Textos livres (ex.: ``Instagram``) são preservados.
    """
    text = " ".join((value or "").split())
    if not text:
        return None
    if text.casefold() in _DEVICE_CHANNELS:
        text = text.upper()
    return text[:MAX_CHANNEL_LENGTH]


def truncate_text(value: str | None, limit: int) -> str | None:
    """Texto sem espaços nas pontas, cortado no limite da coluna.

    Campos descritivos (título, canal, status bruto) são cortados em vez de
    rejeitados: o valor original permanece em ``imported_rows.raw_data`` e uma
    linha inteira não é perdida por causa de um nome de produto comprido.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text[:limit]
