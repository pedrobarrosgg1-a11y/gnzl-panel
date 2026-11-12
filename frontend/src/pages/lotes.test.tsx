import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../App";
import type {
  LinkBatchDetail,
  LinkBatchSummary,
  Product,
  ProductListSummary,
  SystemConfig,
} from "../types/api";

const config: SystemConfig = {
  version: "0.1.0",
  environment: "dev",
  provider: "demo",
  is_demo: true,
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

const listSummary: ProductListSummary = {
  id: 7,
  name: "Black Friday",
  description: null,
  item_count: 2,
  created_at: "2026-11-01T12:00:00Z",
  updated_at: "2026-11-01T12:00:00Z",
};

const pendingDetail: LinkBatchDetail = {
  id: 9,
  name: "Campanha de verão",
  destination_type: "list",
  product_list_id: 7,
  observation: null,
  sub_id_1: "instagram",
  sub_id_2: null,
  sub_id_3: null,
  sub_id_4: null,
  sub_id_5: null,
  source: "demo",
  is_demo: true,
  total_items: 2,
  successful_items: 0,
  failed_items: 0,
  status: "pending",
  created_at: "2026-11-10T12:00:00Z",
  finished_at: null,
  items: [
    {
      id: 1,
      product_id: fone.id,
      product: fone,
      original_url: fone.product_url ?? "",
      status: "pending",
      affiliate_link_id: null,
      affiliate_url: null,
      error_code: null,
      error_message: null,
      attempts: 0,
      processed_at: null,
      created_at: "2026-11-10T12:00:00Z",
    },
    {
      id: 2,
      product_id: cadeira.id,
      product: cadeira,
      original_url: cadeira.product_url ?? "",
      status: "pending",
      affiliate_link_id: null,
      affiliate_url: null,
      error_code: null,
      error_message: null,
      attempts: 0,
      processed_at: null,
      created_at: "2026-11-10T12:00:00Z",
    },
  ],
};

const completedDetail: LinkBatchDetail = {
  ...pendingDetail,
  successful_items: 2,
  status: "completed",
  finished_at: "2026-11-10T12:01:00Z",
  items: [
    {
      ...pendingDetail.items[0],
      status: "success",
      affiliate_link_id: 31,
      affiliate_url: "https://demo.gnzl.local/r/fone",
      attempts: 1,
      processed_at: "2026-11-10T12:01:00Z",
    },
    {
      ...pendingDetail.items[1],
      status: "success",
      affiliate_link_id: 32,
      affiliate_url: "https://demo.gnzl.local/r/cadeira",
      attempts: 1,
      processed_at: "2026-11-10T12:01:00Z",
    },
  ],
};

const summary: LinkBatchSummary = {
  id: 9,
  name: "Campanha de verão",
  destination_type: "list",
  product_list_id: 7,
  observation: null,
  sub_id_1: "instagram",
  sub_id_2: null,
  sub_id_3: null,
  sub_id_4: null,
  sub_id_5: null,
  source: "demo",
  is_demo: true,
  total_items: 2,
  successful_items: 2,
  failed_items: 0,
  status: "completed",
  created_at: "2026-11-10T12:00:00Z",
  finished_at: "2026-11-10T12:01:00Z",
};

function jsonResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  } as unknown as Response;
}

function errorResponse(status: number, code: string, message: string): Response {
  return jsonResponse(
    { error: { code, message, details: null, request_id: null } },
    status,
  );
}

function emptyBatches() {
  return {
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    has_next: false,
  };
}

type RouteHandler = (
  url: URL,
  init: RequestInit,
) => Promise<Response> | undefined;

function installApi(handler: RouteHandler) {
  const fetchMock = vi.fn(
    (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = new URL(String(input), "http://localhost");

      if (url.pathname === "/api/config") {
        return Promise.resolve(jsonResponse(config));
      }

      const response = handler(url, init);
      if (response) {
        return response;
      }

      return Promise.reject(
        new Error(`rota inesperada: ${url.pathname} (${init.method ?? "GET"})`),
      );
    },
  );

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  );
}

function renderProductSelection() {
  return render(
    <MemoryRouter
      initialEntries={[
        {
          pathname: "/lotes",
          search: "?produtos=1,2",
          state: { products: [fone, cadeira] },
        },
      ]}
    >
      <AppRoutes />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete (navigator as unknown as { clipboard?: unknown }).clipboard;
});

describe("lotes", () => {
  it("lista os lotes e abre o detalhe", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(
          jsonResponse({
            items: [summary],
            page: 1,
            page_size: 20,
            total: 1,
            has_next: false,
          }),
        );
      }
      if (url.pathname === "/api/lists") {
        return Promise.resolve(jsonResponse([listSummary]));
      }
      if (url.pathname === "/api/link-batches/9") {
        return Promise.resolve(jsonResponse(completedDetail));
      }
      return undefined;
    });

    renderAt("/lotes");

    expect(await screen.findByText("concluído")).toBeInTheDocument();
    expect(screen.getByText("2 de 2 links")).toBeInTheDocument();
    expect(screen.getByText("lista #7")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("link", { name: "Campanha de verão" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Campanha de verão", level: 1 }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("https://demo.gnzl.local/r/fone"),
    ).toBeInTheDocument();
  });

  it("cria um lote a partir da lista indicada na url", async () => {
    let createBody: unknown = null;

    installApi((url, init) => {
      if (url.pathname === "/api/lists") {
        return Promise.resolve(jsonResponse([listSummary]));
      }
      if (url.pathname === "/api/link-batches" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(emptyBatches()));
      }
      if (url.pathname === "/api/link-batches" && init.method === "POST") {
        createBody = JSON.parse(String(init.body));
        return Promise.resolve(jsonResponse(pendingDetail, 201));
      }
      if (url.pathname === "/api/link-batches/9") {
        return Promise.resolve(jsonResponse(pendingDetail));
      }
      return undefined;
    });

    renderAt("/lotes?lista=7");

    await screen.findByRole("option", { name: /Black Friday/ });
    expect(
      (screen.getByLabelText("lista de origem") as HTMLSelectElement).value,
    ).toBe("7");

    fireEvent.change(screen.getByLabelText("nome do lote"), {
      target: { value: "Campanha de verão" },
    });
    fireEvent.change(screen.getByLabelText("sub id 1"), {
      target: { value: "Instagram" },
    });
    fireEvent.click(screen.getByRole("button", { name: "criar lote" }));

    expect(
      await screen.findByRole("heading", {
        name: "Campanha de verão",
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(createBody).toEqual({
      name: "Campanha de verão",
      destination_type: "list",
      product_ids: [],
      product_list_id: 7,
      observation: null,
      sub_id_1: "Instagram",
      sub_id_2: null,
      sub_id_3: null,
      sub_id_4: null,
      sub_id_5: null,
    });
    expect(
      screen.getByText("lote criado com 2 itens. os links ainda não foram gerados."),
    ).toBeInTheDocument();
  });

  it("cria um lote com os produtos selecionados na busca", async () => {
    let createBody: unknown = null;

    installApi((url, init) => {
      if (url.pathname === "/api/lists") {
        return Promise.resolve(jsonResponse([listSummary]));
      }
      if (url.pathname === "/api/link-batches" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(emptyBatches()));
      }
      if (url.pathname === "/api/link-batches" && init.method === "POST") {
        createBody = JSON.parse(String(init.body));
        return Promise.resolve(
          jsonResponse({ ...pendingDetail, destination_type: "product", product_list_id: null }, 201),
        );
      }
      if (url.pathname === "/api/link-batches/9") {
        return Promise.resolve(
          jsonResponse({ ...pendingDetail, destination_type: "product", product_list_id: null }),
        );
      }
      return undefined;
    });

    renderProductSelection();

    expect(
      await screen.findByText("2 produtos selecionados"),
    ).toBeInTheDocument();
    expect(screen.getByText(fone.title)).toBeInTheDocument();
    expect(screen.getByText(cadeira.title)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("nome do lote"), {
      target: { value: "Seleção da busca" },
    });
    fireEvent.click(screen.getByRole("button", { name: "criar lote" }));

    await waitFor(() => {
      expect(createBody).toMatchObject({
        name: "Seleção da busca",
        destination_type: "product",
        product_ids: [1, 2],
        product_list_id: null,
      });
    });
  });

  it("executa o lote e mostra os links gerados", async () => {
    let runCalled = false;

    installApi((url, init) => {
      if (url.pathname === "/api/link-batches/9" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(pendingDetail));
      }
      if (url.pathname === "/api/link-batches/9/run" && init.method === "POST") {
        runCalled = true;
        return Promise.resolve(jsonResponse(completedDetail));
      }
      return undefined;
    });

    renderAt("/lotes/9");

    expect(await screen.findByText(fone.title)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "gerar links" }));

    expect(await screen.findByText("2 links gerados.")).toBeInTheDocument();
    expect(runCalled).toBe(true);
    expect(
      screen.getByText("https://demo.gnzl.local/r/cadeira"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "gerar links" }),
    ).not.toBeInTheDocument();
  });

  it("explica o conflito quando o lote já está em execução", async () => {
    installApi((url, init) => {
      if (url.pathname === "/api/link-batches/9" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(pendingDetail));
      }
      if (url.pathname === "/api/link-batches/9/run" && init.method === "POST") {
        return Promise.resolve(
          errorResponse(409, "conflict", "Este lote já está em execução."),
        );
      }
      return undefined;
    });

    renderAt("/lotes/9");

    fireEvent.click(await screen.findByRole("button", { name: "gerar links" }));

    expect(
      await screen.findByText("Este lote já está em execução."),
    ).toBeInTheDocument();
  });

  it("copia o link de um item do lote", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    installApi((url) => {
      if (url.pathname === "/api/link-batches/9") {
        return Promise.resolve(jsonResponse(completedDetail));
      }
      return undefined;
    });

    renderAt("/lotes/9");

    fireEvent.click(
      await screen.findByRole("button", {
        name: `copiar link de "${fone.title}"`,
      }),
    );

    expect(
      await screen.findByText(`link de "${fone.title}" copiado.`),
    ).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith("https://demo.gnzl.local/r/fone");
  });

  it("explica quando o lote não existe", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches/99") {
        return Promise.resolve(
          errorResponse(404, "not_found", "Lote não encontrado."),
        );
      }
      return undefined;
    });

    renderAt("/lotes/99");

    expect(
      await screen.findByRole("heading", { name: "lote não encontrado" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "voltar para lotes" }),
    ).toHaveAttribute("href", "/lotes");
  });
});
