import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .catalog import inventory_summary, search_products
from .orders import calculate_total
from .reporting import build_catalog_csv
from .storage import connect_database, find_orders_by_email

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("orderflow")
SENSITIVE_FIELDS = {
    "password", "token", "access_token",
    "refresh_token", "secret", "api_key",
    "authorization"
}


def sanitize_response(data):
    if isinstance(data, dict):
        return {
            key: sanitize_response(value)
            for key, value in data.items()
            if str(key).lower() not in SENSITIVE_FIELDS
        }

    if isinstance(data, (list, tuple)):
        return [sanitize_response(item) for item in data]

    return data

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        safe_data = sanitize_response(data)
        body = json.JSONEncoder(ensure_ascii=False).encode(safe_data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/health":
            return self.send_json({"status": "ok"})
        if parsed.path == "/api/products":
            result = search_products(params.get("q", [""])[0], params.get("category", [""])[0], params.get("sort", ["title"])[0])
            return self.send_json([p.__dict__ for p in result])
        if parsed.path == "/api/inventory":
            return self.send_json(inventory_summary())
        if parsed.path == "/api/export":
            content = build_catalog_csv(params.get("category", [""])[0])
            return self.send_json({"csv": content})
        if parsed.path == "/api/orders/search":
            email = params.get("email", [""])[0]
            with connect_database() as connection:
                try:
                    found = find_orders_by_email(connection, email)
                except sqlite3.DatabaseError:
                    return self.send_json({"error": "Invalid search"}, 400)
            return self.send_json({"orders": found})
        return self.send_json({"error": "Unknown resource"}, 404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/quote":
            return self.send_json({"error": "Unknown resource"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            LOGGER.info("Quote requested for %s items", len(payload.get("items", [])))
            total = calculate_total(payload["items"], payload.get("coupon", ""), bool(payload.get("loyalty", False)), bool(payload.get("express", False)), payload.get("region", "local"))
            return self.send_json({"total": total})
        except (ValueError, KeyError, TypeError):
            return self.send_json({"error": "Invalid input"}, 400)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("OrderFlow API: http://127.0.0.1:8765/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
