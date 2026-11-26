"""Unit tests for scripts/audit_contracts.py."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit_contracts.py"
SPEC = importlib.util.spec_from_file_location("audit_contracts", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def make_min_task(root: Path, name: str = "demo") -> Path:
    task = root / name
    (task / "environment/seed").mkdir(parents=True, exist_ok=True)
    (task / "tests/fixtures/cicd").mkdir(parents=True, exist_ok=True)
    (task / "tests/websitebench/harbor").mkdir(parents=True, exist_ok=True)
    (task / "environment/seed/scored-interfaces.json").write_text(
        json.dumps(
            {
                "schema": "websitebench.harbor.scored-interface-contract",
                "site_id": name,
                "interfaces": [],
            }
        ),
        encoding="utf-8",
    )
    return task


class AuditContractsTests(unittest.TestCase):
    def test_normalize_contract_path_generalizes_ids_and_slugs(self):
        cases = {
            "/api/bookings/${t1-discovery-action-4:/json/booking/booking_id}/cancel": "/api/bookings/{id}/cancel",
            "/app/quote/00000000-0000-4000-8000-00000000d001/company-information": "/app/quote/{id}/company-information",
            "/api/orders/CR-999999/cancel": "/api/orders/{id}/cancel",
            "/weekly-menu/2026-W37/select": "/weekly-menu/{week}/select",
            "/shop/product/mgf64ll/a/iphone-17-pro-techwoven-case-with-magsafe-sienna": "/shop/product/{sku}/{slug}",
            "/eyeglasses/percey/chestnut-crystal/atc": "/eyeglasses/{model}/{color}/atc",
            "/new-york-conversations/join": "/{group}/join",
            "/learning/bookmarks/lesson-neural-intro": "/learning/bookmarks/{slug}",
            "/donate/make-block-bloom": "/donate/{slug}",
            "/p/lisbon-baixa-riverside-inn/review/rv-seed-member-3/edit": "/p/{slug}/review/{id}/edit",
        }
        for raw, expected in cases.items():
            self.assertEqual(audit.normalize_contract_path(raw), expected, raw)

    def test_is_clean_contract_path_filters_negative_and_prefix_paths(self):
        self.assertFalse(audit.is_clean_contract_path("/"))
        self.assertFalse(audit.is_clean_contract_path("/healthz"))
        self.assertFalse(audit.is_clean_contract_path("/api/bases/"))
        self.assertFalse(audit.is_clean_contract_path("/api/items/missing"))
        self.assertFalse(audit.is_clean_contract_path("/api/items/not-a-real-id"))
        self.assertFalse(audit.is_clean_contract_path("/static/app.js"))
        self.assertFalse(
            audit.is_clean_contract_path("/__admin/reset", {"/__admin/reset"})
        )
        self.assertTrue(audit.is_clean_contract_path("/api/items/{slug}"))

    def test_path_matches_pattern_supports_params_and_wildcards(self):
        self.assertTrue(
            audit.path_matches_pattern("/api/bookings/42", "/api/bookings/{id}")
        )
        self.assertTrue(
            audit.path_matches_pattern("/api/bookings/{id}", "/api/bookings/42")
        )
        self.assertTrue(audit.path_matches_pattern("/api/checkout", "/api/*"))
        self.assertFalse(
            audit.path_matches_pattern("/api/bookings/42/cancel", "/api/bookings/{id}")
        )

    def test_extractors_and_sync_idempotency(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            task = make_min_task(root, "demo")
            (task / "environment/seed/scored-interfaces.json").write_text(
                json.dumps(
                    {
                        "schema": "websitebench.harbor.scored-interface-contract",
                        "site_id": "demo",
                        "interfaces": [
                            {
                                "id": "runtime-health",
                                "path": "/__websitebench/health",
                                "methods": ["GET"],
                                "summary": "Health",
                                "request": ["GET /__websitebench/health"],
                                "behavior": ["Returns ok."],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/fixtures/task-suite.json").write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "id": "demo-t1-0000",
                                "actions": [
                                    {
                                        "op": "api",
                                        "method": "POST",
                                        "path": "/cart/add",
                                        "headers": {
                                            "content-type": "application/x-www-form-urlencoded"
                                        },
                                        "body": {
                                            "sku": "123",
                                            "websitebench_case": "secret",
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/fixtures/cicd-suite.json").write_text(
                json.dumps(
                    {
                        "checks": [
                            {
                                "arguments": [
                                    "--assertion",
                                    "all-writes-remain-under-data-dir",
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/fixtures/cicd/obligations.json").write_text(
                json.dumps(
                    {
                        "management_probes": [
                            {"method": "POST", "path": "/__admin/reset"}
                        ],
                        "business_probe": {
                            "baseline": {"method": "GET", "path": "/cart"},
                            "mutate": {
                                "method": "POST",
                                "path": "/api/orders",
                                "headers": {"content-type": "application/json"},
                                "body": {"plan": "pro"},
                            },
                            "read": {"method": "GET", "path": "/api/orders"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/websitebench/harbor/demo_laws.py").write_text(
                "def check(h):\n"
                "    if path.startswith('/api/internal-guard'):\n"
                "        pass\n"
                "    h.api('/api/profile', {'name': 'Alice'}, method='PATCH')\n"
                "    h.urlopen('/api/catalog')\n"
                "    h.api('/api/items/' + item_id)\n",
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    audit.main(["--root", str(root), "--check"]),
                    1,
                )
                self.assertEqual(
                    audit.main(["--root", str(root), "--sync"]),
                    0,
                )
                self.assertEqual(
                    audit.main(["--root", str(root), "--check"]),
                    0,
                )

            si = json.loads(
                (task / "environment/seed/scored-interfaces.json").read_text(
                    encoding="utf-8"
                )
            )
            by_path = {it["path"]: it for it in si["interfaces"]}
            self.assertIn("/healthz", by_path)
            self.assertNotIn("/__websitebench/health", by_path)
            self.assertEqual(by_path["/cart/add"]["methods"], ["POST"])
            self.assertNotIn("websitebench_case", json.dumps(by_path["/cart/add"]))
            self.assertIn("sku", json.dumps(by_path["/cart/add"]))
            self.assertEqual(by_path["/api/orders"]["methods"], ["GET", "POST"])
            self.assertEqual(by_path["/api/profile"]["methods"], ["PATCH"])
            self.assertEqual(by_path["/api/catalog"]["methods"], ["GET"])
            self.assertNotIn("/api/internal-guard", by_path)
            self.assertNotIn("/api/items/", by_path)
            self.assertNotIn("/__admin/reset", by_path)

            # Second sync is a no-op
            self.assertFalse(audit.sync_task(task))

    def test_inactive_business_probe_is_ignored(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            task = make_min_task(root, "inactive")
            (task / "tests/fixtures/cicd-suite.json").write_text(
                json.dumps(
                    {
                        "checks": [
                            {
                                "arguments": [
                                    "--assertion",
                                    "runtime-writes-stay-under-data-dir",
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/fixtures/cicd/obligations.json").write_text(
                json.dumps(
                    {
                        "business_probe": {
                            "baseline": {"method": "GET", "path": "/"},
                            "mutate": {"method": "POST", "path": "/api/auth/signup"},
                            "read": {"method": "GET", "path": "/"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            res = audit.audit_task(task)
            self.assertEqual(res["missing_interfaces"], {})

    def test_active_mail_and_payment_probes_extract_non_secret_steps(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            task = make_min_task(root, "mailpay")
            (task / "tests/fixtures/cicd-suite.json").write_text(
                json.dumps(
                    {
                        "checks": [
                            {
                                "arguments": [
                                    "--assertion",
                                    "mailbox-purposes-use-only-local-sidecar",
                                ]
                            },
                            {
                                "arguments": [
                                    "--assertion",
                                    "local-sandbox-payment-never-creates-live-charge",
                                ]
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (task / "tests/fixtures/v2/cicd/obligations.json").parent.mkdir(
                parents=True, exist_ok=True
            )
            (task / "tests/fixtures/v2/cicd/obligations.json").write_text(
                json.dumps(
                    {
                        "effect_policy": "payment-sandbox",
                        "mail_probe": {
                            "method": "POST",
                            "path": "/recover",
                            "headers": {
                                "content-type": "application/x-www-form-urlencoded"
                            },
                            "body": {"email": "buyer@example.test"},
                        },
                        "payment_probe": {
                            "method": "POST",
                            "path": "/checkout",
                            "headers": {"content-type": "application/json"},
                            "body": {"plan": "pro"},
                            "prerequisites": [
                                {
                                    "method": "POST",
                                    "path": "/auth/register",
                                    "body": {"email": "buyer@example.test"},
                                },
                                {
                                    "method": "POST",
                                    "path": "/auth/login",
                                    "body": {
                                        "email": "buyer@example.test",
                                        "password": {"evaluator_secret": "primary"},
                                    },
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            res = audit.audit_task(task)
            self.assertIn("/recover", res["missing_interfaces"])
            self.assertIn("/checkout", res["missing_interfaces"])
            self.assertIn("/auth/register", res["missing_interfaces"])
            self.assertNotIn("/auth/login", res["missing_interfaces"])


if __name__ == "__main__":
    unittest.main()
