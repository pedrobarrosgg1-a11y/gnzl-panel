"""Serviço de histórico e regeneração de links."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ProviderInvalidResponse
from app.models.link import AffiliateLink
from app.providers.base import LinkProvider
from app.repositories import links as links_repo
from app.services.normalization import normalize_sub_id_slots
from app.services.sub_ids import SubIdService

_SUB_ID_DIMENSIONS = ("sub_id_1", "sub_id_2", "sub_id_3", "sub_id_4", "sub_id_5")


def _link_values(link: AffiliateLink) -> tuple[str | None, ...]:
    return (
        link.sub_id_1,
        link.sub_id_2,
        link.sub_id_3,
        link.sub_id_4,
        link.sub_id_5,
    )


class LinkService:
    def __init__(
        self,
        session: Session,
        link_provider: LinkProvider,
        *,
        source: str,
    ) -> None:
        self._session = session
        self._provider = link_provider
        self._source = source

    def list_page(
        self,
        *,
        term: str | None,
        batch_id: int | None,
        status: str | None,
        sub_id_1: str | None,
        sub_id_2: str | None,
        sub_id_3: str | None,
        data_source: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AffiliateLink], int]:
        return links_repo.search(
            self._session,
            term=term,
            batch_id=batch_id,
            status=status,
            sub_id_1=sub_id_1,
            sub_id_2=sub_id_2,
            sub_id_3=sub_id_3,
            data_source=data_source,
            page=page,
            page_size=page_size,
        )

    def get(self, link_id: int) -> AffiliateLink:
        link = links_repo.get_by_id(self._session, link_id)
        if link is None:
            raise NotFoundError("Link não encontrado.")
        return link

    def regenerate(
        self,
        link_id: int,
        *,
        sub_ids: Sequence[str | None] | None,
        observation: str | None,
        update_observation: bool,
    ) -> AffiliateLink:
        """Cria um novo link e marca o anterior como substituído.

        ``sub_ids=None`` reaproveita a configuração atual. Nesse caso a URL
        gerada é a mesma e a operação é recusada — regenerar sem mudar nada
        só criaria histórico vazio.
        """
        previous = self.get(link_id)
        if previous.status != "active":
            raise ConflictError("Somente links ativos podem ser regenerados.")
        if previous.data_source != self._source:
            raise ConflictError(
                "Este link pertence a outra origem de dados. "
                "Ative o provedor correspondente para regenerá-lo.",
                details={
                    "link_source": previous.data_source,
                    "active_source": self._source,
                },
            )

        effective_values = (
            normalize_sub_id_slots(sub_ids)
            if sub_ids is not None
            else _link_values(previous)
        )
        provider_sub_ids = tuple(value for value in effective_values if value)
        generated = self._provider.create_link(
            previous.original_url, provider_sub_ids
        )
        if not generated.affiliate_url.strip():
            raise ProviderInvalidResponse("O provedor retornou um link vazio.")

        existing = links_repo.get_by_affiliate_url(
            self._session, generated.affiliate_url
        )
        if existing is not None:
            if existing.id == previous.id:
                raise ConflictError(
                    "Os Sub IDs atuais geram o mesmo link. Altere-os para regenerar."
                )
            raise ConflictError(
                "Já existe um link com essa URL.",
                details={"link_id": existing.id},
            )

        new_link = AffiliateLink(
            product=previous.product,
            link_batch_id=previous.link_batch_id,
            original_url=previous.original_url,
            affiliate_url=generated.affiliate_url,
            sub_id_1=effective_values[0],
            sub_id_2=effective_values[1],
            sub_id_3=effective_values[2],
            sub_id_4=effective_values[3],
            sub_id_5=effective_values[4],
            observation=observation if update_observation else previous.observation,
            status="active",
            data_source=previous.data_source,
        )
        self._session.add(new_link)
        self._session.flush()

        previous.status = "replaced"
        previous.replaced_by_id = new_link.id

        values = {
            dimension: value
            for dimension, value in zip(_SUB_ID_DIMENSIONS, effective_values)
            if value
        }
        if values:
            SubIdService(self._session).register_usage(values)

        self._session.commit()
        return new_link
