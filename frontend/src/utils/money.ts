const moneyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const numberFormatter = new Intl.NumberFormat("pt-BR");

const decimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function decimalStringToNumber(raw: string): number | null {
  const cleaned = raw.replace(/[R$\s]/gi, "");
  if (!cleaned) {
    return null;
  }

  let normalized = cleaned;
  if (cleaned.includes(",")) {
    // Formato brasileiro: ponto separa milhar, vírgula separa centavos.
    normalized = cleaned.replace(/\./g, "").replace(",", ".");
  } else if ((cleaned.match(/\./g) ?? []).length > 1) {
    // "1.234.567" sem vírgula: pontos são separadores de milhar.
    normalized = cleaned.replace(/\./g, "");
  }

  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) {
    return null;
  }

  return Number(normalized);
}

/** Converte um valor digitado em reais para centavos. */
export function parseBRLToCents(raw: string): number | null {
  const value = decimalStringToNumber(raw);
  if (value === null || value < 0) {
    return null;
  }
  return Math.round(value * 100);
}

/** Converte um percentual digitado (ex.: "12,5") para pontos-base. */
export function parsePercentToBp(raw: string): number | null {
  const value = decimalStringToNumber(raw.replace("%", ""));
  if (value === null || value < 0 || value > 100) {
    return null;
  }
  return Math.round(value * 100);
}

export function formatBRL(cents: number): string {
  return moneyFormatter.format(cents / 100);
}

export function formatPercentFromBp(basisPoints: number): string {
  return `${decimalFormatter.format(basisPoints / 100)}%`;
}

export function formatInteger(value: number | null): string {
  return value === null ? "—" : numberFormatter.format(value);
}

export function formatRating(ratingX100: number | null): string {
  return ratingX100 === null ? "—" : decimalFormatter.format(ratingX100 / 100);
}
