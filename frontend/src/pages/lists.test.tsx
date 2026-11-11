import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppRoutes } from "../App";
import type {
  Product,
  ProductListDetail,
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

const summary: ProductListSummary = {
  id: 1,
  name: "Black Friday",
  description: null,
  item_count: 0,
  created_at: "2026-11-01T12:00:00Z",
  updated_at: "2026-11-01T12:00:00Z",
};

function jsonResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  } as unknown as Response;
}

function noContent(): Response {
  return {
    ok: true,
    status: 204,
    json: async () => null,
  } as unknown as Response;
}

function errorResponse(status: number, code: string, message: string): Response {
  return jsonResponse(
    { error: { code, message, details: null, request_id: null } },
    status,
  );
}

type RouteHandler = (
  pathname: string,
  init: RequestInit,
) => Promise<Response> | undefined;

function installApi(handler: RouteHandler) {
  const fetchMock = vi.fn(
    (input: RequestInfo | URL, init: RequestInit = {}) => {
      const pathname = new URL(String(input), "http://localhost").pathname;

      if (pathname === "/api/config") {
        return Promise.resolve(jsonResponse(config));
      }

      const response = handler(pathname, init);
      if (response) {
        return response;
      }

      return Promise.reject(
        new Error(`rota inesperada: ${pathname} (${init.method ?? "GET"})`),
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

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("listas", () => {
  it("cria uma lista e mostra o atalho para o detalhe", async () => {
    let lists: ProductListSummary[] = [];
    let createBody: unknown = null;

    installApi((pathname, init) => {
      if (pathname === "/api/lists" && !init.method) {
        return Promise.resolve(jsonResponse(lists));
      }
      if (pathname === "/api/lists" && init.method === "POST") {
        createBody = JSON.parse(String(init.body));
        const created = { ...summary };
        lists = [created];
        return Promise.resolve(jsonResponse(created, 201));
      }
      return undefined;
    });

    renderAt("/listas");

    expect(
      await screen.findByRole("heading", { name: "nenhuma lista ainda" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("nome"), {
      target: { value: "  Black Friday  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "criar lista" }));

    expect(
      await screen.findByText('lista "Black Friday" criada.'),
    ).toBeInTheDocument();
    expect(createBody).toEqual({ name: "Black Friday", description: null });
    expect(screen.getByRole("link", { name: "Black Friday" })).toHaveAttribute(
      "href",
      "/listas/1",
    );
  });

  it("mostra o conflito de nome devolvido pela API", async () => {
    installApi((pathname, init) => {
      if (pathname === "/api/lists" && !init.method) {
        return Promise.resolve(jsonResponse([]));
      }
      if (pathname === "/api/lists" && init.method === "POST") {
        return Promise.resolve(
          errorResponse(409, "conflict", "Já existe uma lista com esse nome."),
        );
      }
      return undefined;
    });

    renderAt("/listas");

    await screen.findByRole("heading", { name: "nenhuma lista ainda" });
    fireEvent.change(screen.getByLabelText("nome"), {
      target: { value: "Black Friday" },
    });
    fireEvent.click(screen.getByRole("button", { name: "criar lista" }));

    expect(
      await screen.findByText("Já existe uma lista com esse nome."),
    ).toBeInTheDocument();
  });

  it("edita o nome da lista no detalhe", async () => {
    const detail: ProductListDetail = {
      ...summary,
      item_count: 1,
      items: [fone],
    };
    let updateBody: unknown = null;

    installApi((pathname, init) => {
      if (pathname === "/api/lists/1" && !init.method) {
        return Promise.resolve(jsonResponse(detail));
      }
      if (pathname === "/api/lists/1" && init.method === "PATCH") {
        updateBody = JSON.parse(String(init.body));
        return Promise.resolve(
          jsonResponse({ ...summary, name: "Campanha nova" }),
        );
      }
      return undefined;
    });

    renderAt("/listas/1");

    expect(
      await screen.findByRole("heading", { name: "Black Friday" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "editar" }));
    fireEvent.change(screen.getByLabelText("nome"), {
      target: { value: "Campanha nova" },
    });
    fireEvent.click(screen.getByRole("button", { name: "salvar" }));

    expect(await screen.findByText("lista atualizada.")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Campanha nova" }),
    ).toBeInTheDocument();
    expect(updateBody).toEqual({
      name: "Campanha nova",
      description: null,
    });
  });

  it("remove produtos da lista até ela ficar vazia", async () => {
    const detail: ProductListDetail = {
      ...summary,
      item_count: 2,
      items: [fone, cadeira],
    };

    installApi((pathname, init) => {
      if (pathname === "/api/lists/1" && !init.method) {
        return Promise.resolve(jsonResponse(detail));
      }
      if (
        pathname.startsWith("/api/lists/1/items/") &&
        init.method === "DELETE"
      ) {
        return Promise.resolve(noContent());
      }
      return undefined;
    });

    renderAt("/listas/1");

    await screen.findByRole("heading", { name: "Black Friday" });

    fireEvent.click(
      screen.getByRole("button", {
        name: `remover "${fone.title}" da lista`,
      }),
    );

    expect(
      await screen.findByText(`"${fone.title}" removido da lista.`),
    ).toBeInTheDocument();
    expect(screen.queryByText(fone.title)).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: `remover "${cadeira.title}" da lista`,
      }),
    );

    expect(
      await screen.findByRole("heading", { name: "lista vazia" }),
    ).toBeInTheDocument();
  });

  it("exclui a lista depois da confirmação inline", async () => {
    const detail: ProductListDetail = {
      ...summary,
      item_count: 1,
      items: [fone],
    };
    let lists: ProductListSummary[] = [summary];

    installApi((pathname, init) => {
      if (pathname === "/api/lists/1" && !init.method) {
        return Promise.resolve(jsonResponse(detail));
      }
      if (pathname === "/api/lists/1" && init.method === "DELETE") {
        lists = [];
        return Promise.resolve(noContent());
      }
      if (pathname === "/api/lists" && !init.method) {
        return Promise.resolve(jsonResponse(lists));
      }
      return undefined;
    });

    renderAt("/listas/1");

    await screen.findByRole("heading", { name: "Black Friday" });
    fireEvent.click(screen.getByRole("button", { name: "excluir lista" }));

    expect(
      await screen.findByRole("heading", { name: "excluir esta lista?" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "excluir definitivamente" }),
    );

    expect(
      await screen.findByRole("heading", { name: "suas listas" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "nenhuma lista ainda" }),
    ).toBeInTheDocument();
  });

  it("explica quando a lista não existe", async () => {
    installApi((pathname, init) => {
      if (pathname === "/api/lists/99" && !init.method) {
        return Promise.resolve(
          errorResponse(404, "not_found", "Lista não encontrada."),
        );
      }
      return undefined;
    });

    renderAt("/listas/99");

    expect(
      await screen.findByRole("heading", { name: "lista não encontrada" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "voltar para listas" }),
    ).toHaveAttribute("href", "/listas");
  });
});
