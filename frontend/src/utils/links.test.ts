import { describe, expect, it } from "vitest";

import {
  normalizeSubIdInput,
  parseProductIds,
  sameSubIds,
} from "./links";

describe("normalizeSubIdInput", () => {
  it("aplica a mesma forma canônica do backend", () => {
    expect(normalizeSubIdInput(" Black Friday ")).toBe("black-friday");
    expect(normalizeSubIdInput("Stories_de_Verão")).toBe("stories-de-verao");
    expect(normalizeSubIdInput("--whatsapp---grupo--")).toBe("whatsapp-grupo");
  });

  it("devolve null quando nada aproveitável sobra", () => {
    expect(normalizeSubIdInput("")).toBeNull();
    expect(normalizeSubIdInput("   ")).toBeNull();
    expect(normalizeSubIdInput("!!!")).toBeNull();
  });

  it("corta no limite do banco sem terminar em hífen", () => {
    const normalized = normalizeSubIdInput("a".repeat(64) + "-extra");
    expect(normalized).toHaveLength(64);
    expect(normalized?.endsWith("-")).toBe(false);
  });
});

describe("sameSubIds", () => {
  it("compara as cinco posições", () => {
    expect(
      sameSubIds(
        ["instagram", null, null, null, null],
        ["instagram", null, null, null, null],
      ),
    ).toBe(true);
    expect(
      sameSubIds(
        ["instagram", null, null, null, null],
        ["instagram", "stories", null, null, null],
      ),
    ).toBe(false);
  });
});

describe("parseProductIds", () => {
  it("limpa ids repetidos ou inválidos da url", () => {
    expect(parseProductIds("1,2,2,x,0,-3,4")).toEqual([1, 2, 4]);
    expect(parseProductIds(null)).toEqual([]);
    expect(parseProductIds("")).toEqual([]);
  });
});
