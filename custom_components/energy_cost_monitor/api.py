"""Authenticated admin-only application API; no raw SQLite downloads."""

import json
import time
import sqlite3
from pathlib import Path

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components import frontend, panel_custom

from ._core.application import render_report
from ._core.study import Study
from .const import DOMAIN


class ApplicationView(HomeAssistantView):
    url = "/api/energy_cost_monitor/{action}"
    name = "api:energy_cost_monitor:application"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def dispatch(self, request, action, data):
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            raise web.HTTPForbidden()
        runtime = self.hass.data.get(DOMAIN)
        if runtime is None or runtime.application is None:
            raise web.HTTPServiceUnavailable()
        app, engine = runtime.application, runtime.collector.engine
        try:
            if action == "view":
                now = time.time()
                end = int(data.get("end", int(now // 900) * 900))
                start = int(data.get("start", end - 86400))
                result = await app.call(app.store.view, engine, start, end, now=now)
                result["price_error"] = app.price_error
            elif action == "profiles":
                if request.method == "POST":
                    if "activate" in data:
                        await app.call(app.store.activate, data["activate"])
                    else:
                        await app.call(app.store.save_profile, data)
                    app.next_fetch = 0
                result = await app.call(app.store.profiles)
            elif action == "reports":
                if request.method == "POST":
                    ident = await app.call(app.store.freeze, engine, int(data["start"]), int(data["end"]))
                    result = {"id": ident}
                else:
                    result = await app.call(app.store.reports)
            elif action == "report":
                result = await app.call(app.store.report, data["id"])
                format = data.get("format", "json")
                if format != "json":
                    content = render_report(result, format)
                    return web.Response(text=content, content_type="text/html" if format == "html" else "text/csv",
                        headers={"Cache-Control": "no-store", "Content-Disposition": f'attachment; filename="energy-report.{format}"',
                                 "Content-Security-Policy": "default-src 'none'; sandbox", "X-Content-Type-Options": "nosniff"})
            elif action == "market":
                result = {"cache": await app.call(app.store.market_status), "error": app.price_error,
                          "next_fetch": app.next_fetch}
            elif action == "study":
                study = Study(app.store)
                if request.method == "POST":
                    result = await app.call(study.cancel if data.get("cancel") is True else study.configure,
                                            *(() if data.get("cancel") is True else (data,)))
                else:
                    result = await app.call(study.status)
                result = {**result, "error": app.study_error}
            elif action == "history":
                from .history import stage_upload, discard_upload, apply_import, list_uploads, resume_upload
                if request.method == "GET":
                    result = await app.call(list_uploads, self.hass)
                elif data.get("command") == "preview":
                    result = await app.call(stage_upload, self.hass, data["file_id"])
                    result["roles"] = list(engine.config.required_roles)
                elif data.get("command") == "resume":
                    result = await app.call(resume_upload, self.hass, data["id"])
                    result["roles"] = list(engine.config.required_roles)
                elif data.get("command") == "discard":
                    result = await app.call(discard_upload, self.hass, data["id"])
                elif data.get("command") == "import":
                    result = await apply_import(runtime, data)
                else:
                    raise ValueError("invalid_import_command")
            else:
                raise web.HTTPNotFound()
        except (ValueError, KeyError, TypeError, OverflowError):
            return web.json_response({"error": "invalid_request_or_unavailable"}, status=400,
                                     headers={"Cache-Control": "no-store"})
        except (OSError, sqlite3.Error):
            raise web.HTTPServiceUnavailable() from None
        return web.json_response(result, headers={"Cache-Control": "no-store"})

    async def get(self, request, action):
        return await self.dispatch(request, action, dict(request.query))

    async def post(self, request, action):
        if action not in {"profiles", "reports", "study", "history"}:
            raise web.HTTPMethodNotAllowed("POST", ["GET"])
        if request.content_length is not None and request.content_length > 256000:
            raise web.HTTPRequestEntityTooLarge(max_size=256000, actual_size=request.content_length)
        if request.get("hass_user") is None or not request["hass_user"].is_admin:
            raise web.HTTPForbidden()
        body = bytearray()
        async for chunk in request.content.iter_chunked(65536):
            body.extend(chunk)
            if len(body) > 256000:
                raise web.HTTPRequestEntityTooLarge(max_size=256000, actual_size=len(body))
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, UnicodeError):
            raise web.HTTPBadRequest() from None
        return await self.dispatch(request, action, data)


class CardView(HomeAssistantView):
    url = "/energy_cost_monitor/energy-cost-monitor-card.js"
    name = "energy_cost_monitor:card"
    requires_auth = False

    def __init__(self, content):
        self.content = content

    async def get(self, request):
        return web.Response(text=self.content, content_type="application/javascript",
                            headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})


async def register_api(hass):
    if not hass.data.get(f"{DOMAIN}_api_registered"):
        def read_card():
            return (Path(__file__).parent / "frontend/energy-cost-monitor-card.js").read_text(encoding="utf-8")
        content = await hass.async_add_executor_job(read_card)
        hass.http.register_view(ApplicationView(hass))
        hass.http.register_view(CardView(content))
        hass.data[f"{DOMAIN}_api_registered"] = True
    if DOMAIN not in hass.data.get("frontend_panels", {}):
        await panel_custom.async_register_panel(
            hass, frontend_url_path=DOMAIN, webcomponent_name="energy-cost-monitor-panel",
            sidebar_title="Energy Cost Monitor", sidebar_icon="mdi:chart-line",
            module_url="/energy_cost_monitor/energy-cost-monitor-card.js", require_admin=True,
        )


def unregister_panel(hass):
    frontend.async_remove_panel(hass, DOMAIN)
