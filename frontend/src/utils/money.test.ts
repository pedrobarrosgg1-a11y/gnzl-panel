import { describe, expect, it } from "vitest";

import {
  formatBRL,
  formatInteger,
  formatPercentFromBp,
  formatRating,
  parseBRLToCents,
  parsePercentToBp,
} from "./money";

describe("parseBRLToCents", () => {
  it("converte formato brasileiro", () => {
    expect(parseBRLToCents("19,90")).toBe(1990);
    expect(parseBRLToCents("R$ 1.234,56")).toBe(123456);
  });

  it("aceita ponto como separador decimal", () => {
    expect(parseBRLToCents("12.5")).toBe(1250);
  });

  it("rejeita entradas inválidas", () => {
    expect(parseBRLToCents("")).toBeNull();
    expect(parseBRLToCents("abc")).toBeNull();
    expect(parseBRLToCents("-5")).toBeNull();
  });
});

describe("parsePercentToBp", () => {
  it("converte percentual em pontos-base", () => {
    expect(parsePercentToBp("12,5")).toBe(1250);
    expect(parsePercentToBp("10%")).toBe(1000);
    expect(parsePercentToBp("0")).toBe(0);
    expect(parsePercentToBp("100")).toBe(10000);
  });

  it("rejeita valores fora da faixa", () => {
    expect(parsePercentToBp("101")).toBeNull();
    expect(parsePercentToBp("abc")).toBeNull();
  });
});

describe("formatação", () => {
  it("formata moeda em reais", () => {
    expect(formatBRL(12990)).toContain("129,90");
    expect(formatBRL(0)).toContain("0,00");
  });

  it("formata percentual a partir de pontos-base", () => {
    expect(formatPercentFromBp(1200)).toBe("12,00%");
  });

  it("formata inteiros e avaliações", () => {
    expect(formatInteger(4820)).toContain("4.820");
    expect(formatInteger(null)).toBe("—");
    expect(formatRating(470)).toBe("4,70");
    expect(formatRating(null)).toBe("—");
  });
});
