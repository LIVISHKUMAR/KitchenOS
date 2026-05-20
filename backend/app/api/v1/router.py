from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1.endpoints import (
    auth, tenants, branches, users, menu, orders, payments,
    inventory, customers, tables, reports, tax, kot, coupons,
    split_billing, audit, loyalty, recipes, vendors, shifts,
    purchase_orders, aggregator, invoices, websocket,
    webhooks, exports, notifications, search, admin, batch,
    api_keys, pricing, franchise, metrics,
    reservations, feedback, combos, scheduled_reports, order_notes,
    sync, printers, barcode, advanced_inventory, profitability, staff_performance,
    events, graphql, i18n, feature_flags, advanced_analytics,
    qr, demand, custom_reports, search_v2, apm, api_docs,
    scheduler_api, cohorts, performance_api,
    recommendations, menu_schedule, discounts, voice, ocr,
    fast_billing, shifts_v2, ws_v2, floor_plan,
    aggregator_v2, whatsapp, loyalty_v2, multi_outlet,
    ai_features, i18n_v2, open_api, advanced_dashboard,
    razorpay
)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(tables.router, prefix="/tables", tags=["tables"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(tax.router, prefix="/tax", tags=["tax"])
api_router.include_router(kot.router, prefix="/kot", tags=["kot"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["coupons"])
api_router.include_router(split_billing.router, prefix="/split-billing", tags=["split-billing"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(loyalty.router, prefix="/loyalty", tags=["loyalty"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])
api_router.include_router(aggregator.router, prefix="/aggregator", tags=["aggregator"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(batch.router, prefix="/batch", tags=["batch"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(franchise.router, prefix="/franchise", tags=["franchise"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(combos.router, prefix="/combos", tags=["combos"])
api_router.include_router(scheduled_reports.router, prefix="/scheduled-reports", tags=["scheduled-reports"])
api_router.include_router(order_notes.router, prefix="/order-notes", tags=["order-notes"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_router.include_router(barcode.router, prefix="/barcode", tags=["barcode"])
api_router.include_router(advanced_inventory.router, prefix="/advanced-inventory", tags=["advanced-inventory"])
api_router.include_router(profitability.router, prefix="/profitability", tags=["profitability"])
api_router.include_router(staff_performance.router, prefix="/staff-performance", tags=["staff-performance"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(graphql.router, tags=["graphql"])
api_router.include_router(i18n.router, prefix="/i18n", tags=["i18n"])
api_router.include_router(feature_flags.router, prefix="/feature-flags", tags=["feature-flags"])
api_router.include_router(advanced_analytics.router, prefix="/advanced-analytics", tags=["advanced-analytics"])
api_router.include_router(qr.router, prefix="/qr", tags=["qr"])
api_router.include_router(demand.router, prefix="/demand", tags=["demand"])
api_router.include_router(custom_reports.router, prefix="/custom-reports", tags=["custom-reports"])
api_router.include_router(search_v2.router, prefix="/search-v2", tags=["search-v2"])
api_router.include_router(apm.router, prefix="/apm", tags=["apm"])
api_router.include_router(api_docs.router, prefix="/api-docs", tags=["api-docs"])
api_router.include_router(scheduler_api.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(cohorts.router, prefix="/cohorts", tags=["cohorts"])
api_router.include_router(performance_api.router, prefix="/performance", tags=["performance"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(menu_schedule.router, prefix="/menu-schedule", tags=["menu-schedule"])
api_router.include_router(discounts.router, prefix="/discounts", tags=["discounts"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(fast_billing.router, prefix="/fast-billing", tags=["fast-billing"])
api_router.include_router(shifts_v2.router, prefix="/shifts-v2", tags=["shifts-v2"])
api_router.include_router(ws_v2.router, tags=["websocket-v2"])
api_router.include_router(floor_plan.router, prefix="/floor-plan", tags=["floor-plan"])
api_router.include_router(aggregator_v2.router, prefix="/aggregator-v2", tags=["aggregator-v2"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(loyalty_v2.router, prefix="/loyalty-v2", tags=["loyalty-v2"])
api_router.include_router(multi_outlet.router, prefix="/multi-outlet", tags=["multi-outlet"])
api_router.include_router(ai_features.router, prefix="/ai", tags=["ai"])
api_router.include_router(i18n_v2.router, prefix="/i18n-v2", tags=["i18n-v2"])
api_router.include_router(open_api.router, prefix="/open-api", tags=["open-api"])
api_router.include_router(advanced_dashboard.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(razorpay.router, prefix="/razorpay", tags=["razorpay"])

# Customer display events endpoint
from fastapi import APIRouter as _AR, Depends as _Depends
from app.api.dependencies import get_current_user as _get_current_user

display_router = _AR()

@display_router.post("/display/event")
async def push_display_event(
    event_type: str,
    data: dict = None,
    current_user: dict = _Depends(_get_current_user)
):
    """Push event to customer display via WebSocket."""
    from app.infrastructure.websocket_manager import notify_customer_display
    try:
        await notify_customer_display(
            current_user["tenant_id"],
            current_user.get("branch_id"),
            {"type": event_type, "data": data or {}}
        )
    except Exception:
        pass
    return {"status": "sent"}

api_router.include_router(display_router, prefix="/pos", tags=["display"])
