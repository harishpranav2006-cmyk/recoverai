"""RecoverAI Dashboard Pages."""

from dashboard.pages.ai_decisions import render_ai_decisions_page
from dashboard.pages.analytics import render_analytics_page
from dashboard.pages.customers import render_customers_page
from dashboard.pages.overview import render_overview_page
from dashboard.pages.payments import render_payments_page
from dashboard.pages.recovery_queue import render_recovery_queue_page
from dashboard.pages.system import render_system_page

__all__ = [
    "render_overview_page",
    "render_recovery_queue_page",
    "render_payments_page",
    "render_customers_page",
    "render_ai_decisions_page",
    "render_analytics_page",
    "render_system_page",
]
