import { describe, expect, it } from "vitest";

import { formatDate, formatDateTime } from "./datetime";

describe("formatDate", () => {
  it("mostra a data no fuso de Brasília", () => {
    expect(formatDate("2026-11-11T02:30:00Z")).toBe("10/11/2026");
  });

  it("degrada para travessão em valor inválido", () => {
    expect(formatDate("não é data")).toBe("—");
  });
});

describe("formatDateTime", () => {
  it("mostra data e hora no fuso de Brasília", () => {
    expect(formatDateTime("2026-11-11T17:32:00Z")).toBe("11/11/2026, 14:32");
  });

  it("degrada para travessão em valor inválido", () => {
    expect(formatDateTime("")).toBe("—");
  });
});
