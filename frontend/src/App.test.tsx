import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "./App";
import type {
  Product,
  ProductListDetail,
  ProductSearchResponse,
  SystemConfig,
} from "./types/api";

const config: SystemConfig = {
  version: "0.1.0",
  environment: "dev",
  provider: "demo",
  is_demo: true,
  capabilities: {
    category_filter: true,
    price_filter: true,
    commission_filter: true,
    sorts: [
      "relevance",
      "commission_desc",
      "sales_desc",
      "rating_desc",
      "price_asc",
      "price_desc",
    ],
  },
};

const fone: Product = {
  id: 1,
  item_id: 100_000,
  shop_id: 5_000,
  title: "Fone bluetooth com cancelamento de ruído",
  image_url: null,
  product_url: "https://shopee.com.br/fone-i.5000.100000",
  price_cents: 12990,
  commission_rate_bp: 1200,
  sales: 4820,
  rating_x100: 470,
  category: "Eletrônicos",
  source: "demo",
};

const cadeira: Product = {
  id: 2,
  item_id: 200_000,
  shop_id: 7_000,
  title: "Cadeira de escritório ergonômica",
  image_url: null,
  product_url: "https://shopee.com.br/cadeira-i.7000.200000",
  price_cents: 89900,
  commission_rate_bp: 800,
  sales: 930,
  rating_x100: 450,
  category: "Casa",
  source: "demo",
};

const blackFriday: ProductListDetail = {
  id: 7,
  name: "Black Friday",
  description: null,
  item_count: 1,
  created_at: "2026-11-01T12:00:00Z",
  updated_at: "2026-11-01T12:00:00Z",
  items: [fone],
};

function searchResponse(items: Product[]): ProductSearchResponse {
  return {
    items,
    page: 1,
    page_size: 20,
    has_next: false,
    total: items.length,
    source: "demo",
    is_demo: true,
  };
}

function jsonResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  } as unknown as Response;
}

type ExtraRoute = (
  url: string,
  init: RequestInit,
) => Promise<Response> | undefined;

function stubApi(
  search: (url: string) => Promise<Response>,
  extra?: ExtraRoute,
  configOverride?: SystemConfig,
) {
  const fetchMock = vi.fn(
    (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = String(input);
      const pathname = new URL(url, "http://localhost").pathname;

      if (pathname === "/api/config") {
        return Promise.resolve(jsonResponse(configOverride ?? config));
      }
      if (pathname === "/api/products/categories") {
        return Promise.resolve(
          jsonResponse({
            items: ["Eletrônicos", "Casa"],
            source: "demo",
            is_demo: true,
          }),
        );
      }
      if (pathname === "/api/products/search") {
        return search(url);
      }
      if (pathname === "/api/lists" && !init.method) {
        return Promise.resolve(jsonResponse([]));
      }

      const extraResponse = extra?.(url, init);
      if (extraResponse) {
        return extraResponse;
      }

      return Promise.reject(new Error(`rota inesperada: ${url}`));
    },
  );

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function defaultSearch(url: string): Promise<Response> {
  const q = new URL(url, "http://localhost").searchParams.get("q") ?? "";
  const items = q.toLowerCase().includes("zzz") ? [] : [fone];
  return Promise.resolve(jsonResponse(searchResponse(items)));
}

function renderApp(initialEntries: string[] = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AppRoutes />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("carrega a busca e identifica o modo demo", async () => {
    stubApi(defaultSearch);
    renderApp();

    expect(await screen.findByText(fone.title)).toBeInTheDocument();
    expect(screen.getAllByText("modo demo").length).toBeGreaterThan(0);
    expect(screen.getByText("1 achado")).toBeInTheDocument();
    expect(screen.getByLabelText("categoria")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "melhor avaliação" }),
    ).toBeInTheDocument();
  });

  it("esconde filtros e ordenações que a shopee não suporta", async () => {
    const shopeeConfig: SystemConfig = {
      ...config,
      provider: "shopee",
      is_demo: false,
      capabilities: {
        category_filter: false,
        price_filter: false,
        commission_filter: false,
        sorts: [
          "relevance",
          "commission_desc",
          "sales_desc",
          "price_asc",
          "price_desc",
        ],
      },
    };
    stubApi(defaultSearch, undefined, shopeeConfig);
    renderApp(["/?sort=rating_desc"]);

    expect(await screen.findByText(fone.title)).toBeInTheDocument();
    expect(screen.queryByLabelText("categoria")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("preço mínimo")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("preço máximo")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("comissão mínima")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("option", { name: "melhor avaliação" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/a API da shopee não permite filtrar/),
    ).toBeInTheDocument();
  });

  it("envia o termo digitado para a API", async () => {
    const fetchMock = stubApi(defaultSearch);
    renderApp();

    await screen.findByText(fone.title);
    fireEvent.change(screen.getByLabelText("buscar produtos"), {
      target: { value: "fone" },
    });
    fireEvent.click(screen.getByRole("button", { name: "buscar" }));

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes("q=fone"))).toBe(true);
    });
  });

  it("mostra estado vazio quando não há produtos", async () => {
    stubApi(() => Promise.resolve(jsonResponse(searchResponse([]))));
    renderApp();

    expect(
      await screen.findByRole("heading", { name: "nada encontrado" }),
    ).toBeInTheDocument();
  });

  it("mostra erro e permite tentar novamente", async () => {
    stubApi(() => Promise.reject(new TypeError("falha de rede")));
    renderApp();

    expect(
      await screen.findByText("não foi possível buscar"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "tentar novamente" }),
    ).toBeInTheDocument();
  });

  it("navega para a tela de listas", async () => {
    stubApi(defaultSearch);
    renderApp();

    await screen.findByText(fone.title);
    fireEvent.click(screen.getByRole("link", { name: "listas" }));

    expect(
      await screen.findByRole("heading", { name: "suas listas" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "nenhuma lista ainda" }),
    ).toBeInTheDocument();
  });

  it("seleciona produtos na busca e abre a criação de lote", async () => {
    stubApi(defaultSearch, (url) => {
      const pathname = new URL(url, "http://localhost").pathname;
      if (pathname === "/api/link-batches") {
        return Promise.resolve(
          jsonResponse({
            items: [],
            page: 1,
            page_size: 20,
            total: 0,
            has_next: false,
          }),
        );
      }
      return undefined;
    });

    renderApp();

    await screen.findByText(fone.title);
    fireEvent.click(
      screen.getByRole("button", { name: "selecionar produtos" }),
    );
    fireEvent.click(
      screen.getByRole("checkbox", {
        name: `selecionar "${fone.title}"`,
      }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "criar lote com 1 produto" }),
    );

    expect(
      await screen.findByRole("heading", { name: "lotes de links" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("1 produto selecionado"),
    ).toBeInTheDocument();
    expect(screen.getByText(fone.title)).toBeInTheDocument();
  });

  it("adiciona produtos à lista pelo modo lista da busca", async () => {
    let addedItems = [fone];

    stubApi(
      () => Promise.resolve(jsonResponse(searchResponse([fone, cadeira]))),
      (url, init) => {
        const pathname = new URL(url, "http://localhost").pathname;
        if (pathname === "/api/lists/7" && !init.method) {
          return Promise.resolve(
            jsonResponse({
              ...blackFriday,
              items: addedItems,
              item_count: addedItems.length,
            }),
          );
        }
        if (pathname === "/api/lists/7/items" && init.method === "POST") {
          addedItems = [fone, cadeira];
          return Promise.resolve(
            jsonResponse({
              added: 1,
              skipped: 0,
              item_count: addedItems.length,
              items: addedItems,
            }),
          );
        }
        return undefined;
      },
    );

    renderApp(["/?lista=7"]);

    expect(await screen.findByText("Black Friday")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", {
        name: `"${fone.title}" já está na lista`,
      }),
    ).toBeDisabled();

    fireEvent.click(
      screen.getByRole("button", {
        name: `adicionar "${cadeira.title}" à lista "Black Friday"`,
      }),
    );

    expect(
      await screen.findByText(
        `"${cadeira.title}" adicionado a "Black Friday".`,
      ),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("button", {
        name: `"${cadeira.title}" já está na lista`,
      }),
    ).toBeDisabled();

    // A URL manda: enviar filtros e limpá-los não pode sair do modo lista.
    fireEvent.change(screen.getByLabelText("buscar produtos"), {
      target: { value: "cadeira" },
    });
    fireEvent.click(screen.getByRole("button", { name: "buscar" }));

    expect(
      await screen.findByRole("region", {
        name: "modo de adicionar produtos à lista",
      }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "limpar filtros" }));

    expect(
      await screen.findByRole("region", {
        name: "modo de adicionar produtos à lista",
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Black Friday").length).toBeGreaterThan(0);
  });
});
