import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../App";
import type {
  AffiliateLink,
  LinkBatchSummary,
  Product,
  SystemConfig,
} from "../types/api";

const config: SystemConfig = {
  version: "0.1.0",
  environment: "dev",
  provider: "demo",
  is_demo: true,
  capabilities: {
    category_filter: true,
    price_filter: true,
    commission_filter: true,
    conversion_sync: false,
    conversion_window_days: 90,
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

const batchSummary: LinkBatchSummary = {
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

const activeLink: AffiliateLink = {
  id: 31,
  product_id: fone.id,
  product: fone,
  link_batch_id: 9,
  original_url: fone.product_url ?? "",
  affiliate_url: "https://demo.gnzl.local/r/fone",
  sub_id_1: "instagram",
  sub_id_2: "stories",
  sub_id_3: null,
  sub_id_4: null,
  sub_id_5: null,
  observation: "link principal",
  status: "active",
  replaced_by_id: null,
  source: "demo",
  is_demo: true,
  created_at: "2026-11-10T12:00:00Z",
};

const replacedLink: AffiliateLink = {
  ...activeLink,
  id: 30,
  affiliate_url: "https://demo.gnzl.local/r/fone-antigo",
  sub_id_2: null,
  status: "replaced",
  replaced_by_id: 31,
  observation: null,
  created_at: "2026-11-09T12:00:00Z",
};

function linksResponse(
  items: AffiliateLink[],
  page = 1,
  hasNext = false,
  total = items.length,
) {
  return {
    items,
    page,
    page_size: 20,
    total,
    has_next: hasNext,
  };
}

function batchesResponse(items: LinkBatchSummary[] = [batchSummary]) {
  return {
    items,
    page: 1,
    page_size: 100,
    total: items.length,
    has_next: false,
  };
}

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

function linksCalls(fetchMock: ReturnType<typeof installApi>) {
  return fetchMock.mock.calls
    .map((call) => new URL(String(call[0]), "http://localhost"))
    .filter((url) => url.pathname === "/api/links");
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete (navigator as unknown as { clipboard?: unknown }).clipboard;
});

describe("links", () => {
  it("mostra o histórico com produto, sub ids e status", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(
          jsonResponse(linksResponse([activeLink, replacedLink], 1, false, 2)),
        );
      }
      return undefined;
    });

    renderAt("/links");

    // O mesmo produto aparece duas vezes: link ativo e link substituído.
    expect(await screen.findAllByText(fone.title)).toHaveLength(2);
    expect(
      screen.getByText("https://demo.gnzl.local/r/fone"),
    ).toBeInTheDocument();
    expect(screen.getByText("instagram · stories")).toBeInTheDocument();
    expect(screen.getByText("ativo")).toBeInTheDocument();
    expect(screen.getByText("substituído")).toBeInTheDocument();
    expect(screen.getByText("substituído pelo link #31")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "histórico de links" }),
    ).toBeInTheDocument();
  });

  it("envia busca, status e sub id normalizado para a API", async () => {
    const fetchMock = installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      return undefined;
    });

    renderAt("/links");

    await screen.findByText(fone.title);

    fireEvent.change(screen.getByLabelText("buscar links"), {
      target: { value: "fone" },
    });
    fireEvent.change(screen.getByLabelText("status"), {
      target: { value: "active" },
    });
    fireEvent.change(screen.getByLabelText("sub id 1"), {
      target: { value: "Black Friday" },
    });
    fireEvent.click(screen.getByRole("button", { name: "filtrar" }));

    await waitFor(() => {
      const last = linksCalls(fetchMock).at(-1);
      expect(last?.searchParams.get("q")).toBe("fone");
      expect(last?.searchParams.get("status")).toBe("active");
      expect(last?.searchParams.get("sub_id_1")).toBe("black-friday");
      expect(last?.searchParams.get("page")).toBe("1");
    });
  });

  it("não aplica sub id sem letras ou números", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      return undefined;
    });

    renderAt("/links");

    await screen.findByText(fone.title);
    fireEvent.change(screen.getByLabelText("sub id 1"), {
      target: { value: "!!!" },
    });
    fireEvent.click(screen.getByRole("button", { name: "filtrar" }));

    expect(
      await screen.findByText("use letras, números e hífen."),
    ).toBeInTheDocument();
  });

  it("copia o link e confirma sem modal", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      return undefined;
    });

    renderAt("/links");

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

  it("recusa regenerar sem alterar nenhum sub id", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      return undefined;
    });

    renderAt("/links");

    fireEvent.click(
      await screen.findByRole("button", {
        name: `regenerar link de "${fone.title}"`,
      }),
    );

    const panel = screen.getByRole("region", {
      name: "regenerar link #31",
    });
    fireEvent.click(
      within(panel).getByRole("button", { name: "regenerar link" }),
    );

    expect(
      await within(panel).findByText(
        "altere ao menos um sub id para gerar uma url diferente.",
      ),
    ).toBeInTheDocument();
  });

  it("regenera o link com os novos sub ids", async () => {
    let regenerateBody: unknown = null;

    installApi((url, init) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      if (
        url.pathname === "/api/links/31/regenerate" &&
        init.method === "POST"
      ) {
        regenerateBody = JSON.parse(String(init.body));
        return Promise.resolve(
          jsonResponse({
            ...activeLink,
            id: 33,
            affiliate_url: "https://demo.gnzl.local/r/fone-novo",
          }),
        );
      }
      return undefined;
    });

    renderAt("/links");

    fireEvent.click(
      await screen.findByRole("button", {
        name: `regenerar link de "${fone.title}"`,
      }),
    );

    const panel = screen.getByRole("region", {
      name: "regenerar link #31",
    });
    fireEvent.change(within(panel).getByLabelText("sub id 2"), {
      target: { value: "Reels" },
    });
    fireEvent.click(
      within(panel).getByRole("button", { name: "regenerar link" }),
    );

    expect(
      await screen.findByText(
        "novo link #33 gerado. o link anterior foi marcado como substituído.",
      ),
    ).toBeInTheDocument();
    expect(regenerateBody).toEqual({
      sub_id_1: "instagram",
      sub_id_2: "reels",
      sub_id_3: null,
      sub_id_4: null,
      sub_id_5: null,
      observation: "link principal",
    });
    expect(
      screen.queryByRole("region", { name: "regenerar link #31" }),
    ).not.toBeInTheDocument();
  });

  it("mostra o conflito devolvido pela API ao regenerar", async () => {
    installApi((url, init) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links" && init.method !== "POST") {
        return Promise.resolve(jsonResponse(linksResponse([activeLink])));
      }
      if (
        url.pathname === "/api/links/31/regenerate" &&
        init.method === "POST"
      ) {
        return Promise.resolve(
          errorResponse(
            409,
            "conflict",
            "Já existe um link com essa URL.",
          ),
        );
      }
      return undefined;
    });

    renderAt("/links");

    fireEvent.click(
      await screen.findByRole("button", {
        name: `regenerar link de "${fone.title}"`,
      }),
    );

    const panel = screen.getByRole("region", {
      name: "regenerar link #31",
    });
    fireEvent.change(within(panel).getByLabelText("sub id 2"), {
      target: { value: "reels" },
    });
    fireEvent.click(
      within(panel).getByRole("button", { name: "regenerar link" }),
    );

    expect(
      await within(panel).findByText("Já existe um link com essa URL."),
    ).toBeInTheDocument();
  });

  it("pagina o histórico", async () => {
    const fetchMock = installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse()));
      }
      if (url.pathname === "/api/links") {
        const page = Number(url.searchParams.get("page") ?? "1");
        return Promise.resolve(
          jsonResponse(
            page === 1
              ? linksResponse([activeLink, replacedLink], 1, true, 22)
              : linksResponse([replacedLink], 2, false, 22),
          ),
        );
      }
      return undefined;
    });

    renderAt("/links");

    expect(await screen.findByText("página 1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "próxima" }));

    expect(await screen.findByText("página 2")).toBeInTheDocument();
    await waitFor(() => {
      const last = linksCalls(fetchMock).at(-1);
      expect(last?.searchParams.get("page")).toBe("2");
    });
  });

  it("mostra o estado vazio com atalho para criar um lote", async () => {
    installApi((url) => {
      if (url.pathname === "/api/link-batches") {
        return Promise.resolve(jsonResponse(batchesResponse([])));
      }
      if (url.pathname === "/api/links") {
        return Promise.resolve(jsonResponse(linksResponse([])));
      }
      return undefined;
    });

    renderAt("/links");

    expect(
      await screen.findByRole("heading", { name: "nenhum link gerado" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "criar um lote" }),
    ).toHaveAttribute("href", "/lotes");
  });
});
