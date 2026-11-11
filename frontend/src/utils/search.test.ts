import { describe, expect, it } from "vitest";

import {
  buildSearch,
  formValuesFromParams,
  paramsFromValues,
  queryFromParams,
  type SearchFormValues,
} from "./search";

const VALUES: SearchFormValues = {
  q: "fone bluetooth",
  category: "Eletrônicos",
  sort: "price_asc",
  priceMin: "19,90",
  priceMax: "1.234,56",
  commissionMin: "12,5",
};

describe("buildSearch", () => {
  it("converte os campos em parâmetros da API", () => {
    const built = buildSearch(VALUES);

    expect(built.errors).toEqual({});
    expect(built.query).toMatchObject({
      q: "fone bluetooth",
      category: "Eletrônicos",
      sort: "price_asc",
      price_min_cents: 1990,
      price_max_cents: 123456,
      min_commission_rate_bp: 1250,
    });
  });

  it("ignora filtros vazios", () => {
    const built = buildSearch({
      q: "  ",
      category: "",
      sort: "relevance",
      priceMin: "",
      priceMax: "",
      commissionMin: "",
    });

    expect(built.errors).toEqual({});
    expect(built.query).toEqual({ sort: "relevance" });
  });

  it("valida preço mínimo maior que o máximo", () => {
    const built = buildSearch({
      ...VALUES,
      priceMin: "100",
      priceMax: "10",
    });

    expect(built.query).toBeNull();
    expect(built.errors.range).toBeDefined();
  });

  it("valida campos inválidos", () => {
    const built = buildSearch({
      ...VALUES,
      priceMin: "abc",
      commissionMin: "101",
    });

    expect(built.errors.priceMin).toBeDefined();
    expect(built.errors.commissionMin).toBeDefined();
  });
});

describe("formValuesFromParams", () => {
  it("reconstrói o formulário a partir da URL", () => {
    const params = paramsFromValues(VALUES);
    const form = formValuesFromParams(params);

    expect(form.q).toBe(VALUES.q);
    expect(form.category).toBe(VALUES.category);
    expect(form.sort).toBe(VALUES.sort);
    expect(form.priceMin).toBe("19,90");
    expect(form.priceMax).toBe("1234,56");
    expect(form.commissionMin).toBe("12,50");
  });

  it("descarta ordenação desconhecida", () => {
    const form = formValuesFromParams(
      new URLSearchParams("sort=whatever"),
    );

    expect(form.sort).toBe("relevance");
  });
});

describe("queryFromParams", () => {
  it("usa página 1 e tamanho 20 por padrão", () => {
    expect(queryFromParams(new URLSearchParams())).toEqual({
      page: 1,
      page_size: 20,
    });
  });

  it("lê página, filtros e ordenação", () => {
    const query = queryFromParams(
      new URLSearchParams(
        "q=fone&page=3&price_min_cents=1000&min_commission_rate_bp=800&sort=sales_desc",
      ),
    );

    expect(query).toMatchObject({
      q: "fone",
      page: 3,
      page_size: 20,
      price_min_cents: 1000,
      min_commission_rate_bp: 800,
      sort: "sales_desc",
    });
  });
});
