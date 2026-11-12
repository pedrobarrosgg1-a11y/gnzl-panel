import { BrowserRouter, Route, Routes } from "react-router";

import { SystemConfigProvider } from "./hooks/useSystemConfig";
import { AppLayout } from "./layouts/AppLayout";
import { LinkBatchDetailPage } from "./pages/LinkBatchDetailPage";
import { LinkBatchesPage } from "./pages/LinkBatchesPage";
import { LinksPage } from "./pages/LinksPage";
import { ListDetailPage } from "./pages/ListDetailPage";
import { ListsPage } from "./pages/ListsPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { SearchPage } from "./pages/SearchPage";

/**
 * Rotas separadas do BrowserRouter para permitir testes com MemoryRouter.
 */
export function AppRoutes() {
  return (
    <SystemConfigProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<SearchPage />} />
          <Route path="listas" element={<ListsPage />} />
          <Route path="listas/:listId" element={<ListDetailPage />} />
          <Route path="lotes" element={<LinkBatchesPage />} />
          <Route path="lotes/:batchId" element={<LinkBatchDetailPage />} />
          <Route path="links" element={<LinksPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </SystemConfigProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
