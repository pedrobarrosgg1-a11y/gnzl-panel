import { Link } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export function NotFoundPage() {
  return (
    <>
      <PageHeader
        eyebrow="404"
        title="página não encontrada"
        description="o endereço acessado não corresponde a uma tela do painel."
        actions={<DemoBadge />}
      />
      <EmptyState
        title="nada aqui"
        description="confira o endereço digitado ou volte para a busca, que é o ponto de partida do painel."
        action={
          <Link to="/" className="gz-btn gz-btn--primary">
            voltar para a busca
          </Link>
        }
      />
    </>
  );
}
