import { BrowserRouter, Route, Routes } from "react-router";

import { SystemConfigProvider } from "./hooks/useSystemConfig";
import { AppLayout } from "./layouts/AppLayout";
import { ComingSoonPage } from "./pages/ComingSoonPage";
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
          <Route
            path="lotes"
            element={
              <ComingSoonPage
                title="lotes"
                description="os lotes vão executar a geração de links em massa e mostrar o resultado item a item."
                phase="etapa 9"
              />
            }
          />
          <Route
            path="links"
            element={
              <ComingSoonPage
                title="links"
                description="o histórico vai mostrar cada link gerado, com sub ids, status e data."
                phase="etapa 9"
              />
            }
          />
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
