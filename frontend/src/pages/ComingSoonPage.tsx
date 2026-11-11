import { Link } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

interface ComingSoonPageProps {
  title: string;
  description: string;
  phase: string;
}

export function ComingSoonPage({
  title,
  description,
  phase,
}: ComingSoonPageProps) {
  return (
    <>
      <PageHeader
        eyebrow="em construção"
        title={title}
        description={description}
        actions={
          <>
            <span className="gz-badge">{phase}</span>
            <DemoBadge />
          </>
        }
      />
      <EmptyState
        title="esta tela entra em seguida"
        description="a busca de produtos já está pronta. enquanto esta parte não chega, use a busca para encontrar produtos e comparar comissões."
        action={
          <Link to="/" className="gz-btn gz-btn--primary">
            ir para a busca
          </Link>
        }
      />
    </>
  );
}
