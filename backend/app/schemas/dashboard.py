"""Schemas de resposta do dashboard."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.services.dashboard import DashboardReport

DashboardSource = Literal["demo", "shopee", "csv"]


class DashboardTotalsOut(BaseModel):
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int
    conversion_bp: int | None
    average_ticket_cents: int | None


class DashboardComparisonOut(BaseModel):
    previous: int
    absolute: int
    variation_bp: int | None


class DashboardComparisonsOut(BaseModel):
    sales_cents: DashboardComparisonOut
    commission_cents: DashboardComparisonOut
    orders: DashboardComparisonOut
    clicks: DashboardComparisonOut


class DashboardDayOut(BaseModel):
    date: date
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int


class DashboardSubIdOut(BaseModel):
    sub_id_1: str | None
    sales_cents: int
    commission_cents: int
    orders: int
    clicks: int


class DashboardItemOut(BaseModel):
    external_item_id: int
    title: str | None
    sales_cents: int
    commission_cents: int
    orders: int


class DashboardOut(BaseModel):
    source: DashboardSource
    is_demo: bool
    start: date
    end: date
    days: int
    previous_start: date
    previous_end: date
    metrics: DashboardTotalsOut
    comparisons: DashboardComparisonsOut
    daily: list[DashboardDayOut]
    top_sub_ids: list[DashboardSubIdOut]
    top_items: list[DashboardItemOut]

    @classmethod
    def from_report(cls, report: DashboardReport) -> "DashboardOut":
        return cls(
            source=report.source,
            is_demo=report.source == "demo",
            start=report.start,
            end=report.end,
            days=report.days,
            previous_start=report.previous_start,
            previous_end=report.previous_end,
            metrics=DashboardTotalsOut(
                sales_cents=report.totals.sales_cents,
                commission_cents=report.totals.commission_cents,
                orders=report.totals.orders,
                clicks=report.totals.clicks,
                conversion_bp=report.totals.conversion_bp,
                average_ticket_cents=report.totals.average_ticket_cents,
            ),
            comparisons=DashboardComparisonsOut(
                **{
                    name: DashboardComparisonOut(
                        previous=comparison.previous,
                        absolute=comparison.absolute,
                        variation_bp=comparison.variation_bp,
                    )
                    for name, comparison in report.comparisons.items()
                }
            ),
            daily=[
                DashboardDayOut(
                    date=point.day,
                    sales_cents=point.sales_cents,
                    commission_cents=point.commission_cents,
                    orders=point.orders,
                    clicks=point.clicks,
                )
                for point in report.daily
            ],
            top_sub_ids=[
                DashboardSubIdOut(
                    sub_id_1=row.sub_id_1,
                    sales_cents=row.sales_cents,
                    commission_cents=row.commission_cents,
                    orders=row.orders,
                    clicks=row.clicks,
                )
                for row in report.top_sub_ids
            ],
            top_items=[
                DashboardItemOut(
                    external_item_id=row.external_item_id,
                    title=row.title,
                    sales_cents=row.sales_cents,
                    commission_cents=row.commission_cents,
                    orders=row.orders,
                )
                for row in report.top_items
            ],
        )
