import { expect, test, type APIRequestContext } from "@playwright/test";

import type {
  LinkBatchDetail,
  Product,
  ProductListSummary,
  ProductSearchResponse,
} from "../../src/types/api";

const FONE = "Fone bluetooth com cancelamento de ruído";
const FAILING = "Produto de demonstração com falha simulada";

async function findProduct(
  request: APIRequestContext,
  query: string,
  title: string,
): Promise<Product> {
  const response = await request.get(
    `/api/products/search?q=${encodeURIComponent(query)}&page=1&page_size=20`,
  );
  expect(response.ok()).toBeTruthy();

  const data = (await response.json()) as ProductSearchResponse;
  const product = data.items.find((item) => item.title === title);
  if (!product) {
    throw new Error(`produto "${title}" não encontrado na busca por "${query}"`);
  }
  return product;
}

async function createList(
  request: APIRequestContext,
  name: string,
  productIds: number[],
): Promise<ProductListSummary> {
  const created = await request.post("/api/lists", {
    data: { name, description: "lista criada pelos testes E2E" },
  });
  expect(created.status()).toBe(201);
  const list = (await created.json()) as ProductListSummary;

  const added = await request.post(`/api/lists/${list.id}/items`, {
    data: { product_ids: productIds },
  });
  expect(added.ok()).toBeTruthy();

  return list;
}

test("seleção na busca cria lote, gera o link e aparece no histórico de lotes", async ({
  page,
}) => {
  await page.goto("/?q=fone");

  const results = page.getByRole("region", { name: "resultados da busca" });
  await expect(results.getByText(FONE, { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "selecionar produtos" }).click();
  await expect(
    page.getByRole("region", { name: "seleção de produtos para o lote" }),
  ).toBeVisible();

  await page
    .getByRole("checkbox", { name: `selecionar "${FONE}"` })
    .check();
  await expect(page.getByText("1 produto selecionado", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "criar lote com 1 produto" }).click();

  await expect(page).toHaveURL(/\/lotes\?produtos=\d+$/);
  await expect(
    page.getByText("origem · produtos da busca", { exact: true }),
  ).toBeVisible();

  await page.getByLabel("nome do lote").fill("e2e seleção");
  await page.getByLabel("sub id 1").fill("E2E Selecao");
  await page.getByRole("button", { name: "criar lote", exact: true }).click();

  await expect(page).toHaveURL(/\/lotes\/\d+$/);
  await expect(
    page.getByRole("heading", { name: "e2e seleção", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("pendente", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: "gerar links" }).click();

  await expect(page.getByText("concluído", { exact: true })).toBeVisible();
  await expect(page.getByText("1 link gerado.", { exact: true })).toBeVisible();
  await expect(
    page.locator('a[href^="https://demo.gnzl.local/r/"]'),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "ver links" })).toBeVisible();

  await page.goto("/lotes");
  const row = page.getByRole("row", { name: /e2e seleção/ });
  await expect(row).toContainText("concluído");
  await expect(row).toContainText("1 de 1 links");
});

test("lote de lista com item com falha termina parcial e mostra o erro do provedor", async ({
  page,
  request,
}) => {
  const fone = await findProduct(request, "fone", FONE);
  const failing = await findProduct(request, "falha", FAILING);
  const list = await createList(request, "e2e lista com falha", [
    fone.id,
    failing.id,
  ]);

  await page.goto(`/lotes?lista=${list.id}`);
  await expect(page.getByLabel("lista de origem")).toHaveValue(String(list.id));

  await page.getByLabel("nome do lote").fill("e2e lote parcial");
  await page.getByLabel("sub id 1").fill("E2E Falha");
  await page.getByRole("button", { name: "criar lote", exact: true }).click();

  await expect(page).toHaveURL(/\/lotes\/\d+$/);
  await expect(
    page.getByRole("heading", { name: "e2e lote parcial", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("2 itens", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "gerar links" }).click();

  await expect(page.getByText("parcial", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      "1 link gerado e 1 com falha. tente novamente os itens pendentes.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(page.getByText(FAILING, { exact: true })).toBeVisible();
  await expect(page.getByText("provider_unavailable", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "tentar pendentes" }),
  ).toBeVisible();
});

test("histórico filtra por lote e regeneração marca o link anterior como substituído", async ({
  page,
  request,
}) => {
  const fone = await findProduct(request, "fone", FONE);

  const created = await request.post("/api/link-batches", {
    data: {
      name: "e2e regeneração",
      destination_type: "product",
      product_ids: [fone.id],
      sub_id_1: "e2e-regen",
    },
  });
  expect(created.status()).toBe(201);
  const batch = (await created.json()) as LinkBatchDetail;

  const run = await request.post(`/api/link-batches/${batch.id}/run`);
  expect(run.ok()).toBeTruthy();
  const finished = (await run.json()) as LinkBatchDetail;

  const item = finished.items[0];
  if (!item?.affiliate_link_id || !item.affiliate_url) {
    throw new Error("o lote de preparação não gerou um link");
  }
  const oldLinkId = item.affiliate_link_id;
  const oldUrl = item.affiliate_url;

  await page.goto("/links");
  await expect(page.getByText("links gerados", { exact: true })).toBeVisible();
  await page.getByLabel("lote").selectOption(String(batch.id));
  await page.getByRole("button", { name: "filtrar", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`batch_id=${batch.id}`));
  await expect(
    page.getByText(`link #${oldLinkId} · lote #${batch.id} · demo`, {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.getByText(oldUrl, { exact: true })).toBeVisible();

  await page
    .getByRole("button", { name: `regenerar link de "${FONE}"` })
    .click();

  const regenerateForm = page.locator("form").filter({
    has: page.getByRole("heading", { name: /regenerar link #/ }),
  });
  await expect(regenerateForm).toBeVisible();

  // Sem alterar nenhum Sub ID, o cliente bloqueia antes de chamar a API.
  await regenerateForm
    .getByRole("button", { name: "regenerar link", exact: true })
    .click();
  await expect(
    page.getByText("altere ao menos um sub id para gerar uma url diferente.", {
      exact: true,
    }),
  ).toBeVisible();

  await regenerateForm.getByLabel("sub id 2").fill("novo-canal");
  await regenerateForm
    .getByRole("button", { name: "regenerar link", exact: true })
    .click();

  await expect(
    page.getByText(
      /novo link #\d+ gerado\. o link anterior foi marcado como substituído\./,
    ),
  ).toBeVisible();
  await expect(page.getByText("2 links", { exact: true })).toBeVisible();
  await expect(page.getByText("substituído", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/substituído pelo link #\d+/),
  ).toBeVisible();

  await page.getByLabel("status").selectOption("replaced");
  await page.getByRole("button", { name: "filtrar", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`batch_id=${batch.id}.*status=replaced`));
  await expect(page.getByText(oldUrl, { exact: true })).toBeVisible();
  await expect(page.getByText("substituído", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: `regenerar link de "${FONE}"` }),
  ).toHaveCount(0);
});
