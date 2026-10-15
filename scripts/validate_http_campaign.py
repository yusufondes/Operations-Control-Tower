"""Explicit synthetic HTTP regression against a newly owned campaign preview.

Not a browser-render test. All mutations stay in the disposable preview DB.
Read only that preview's temporary credential; never log passwords or cookies.
The owner must remove the preview with preview-dispatch.ps1 after execution.
"""
import http.cookiejar
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


class RPCError(Exception):
    def __init__(self, data):
        self.kind = data.get("name", "RPCError")
        self.message = data.get("message", "Request refused")
        super().__init__(self.kind + ": " + self.message)


def main():
    url, database, container = sys.argv[1:]
    identity = re.fullmatch(r"oct_scenario_([0-9a-f]{32})", database)
    parsed = urlparse(url)
    if not identity or container != "oct-ui-" + identity[1]:
        raise RuntimeError("Unsafe preview identity")
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port or parsed.path:
        raise RuntimeError("Only an owned loopback preview URL is supported")
    credential = Path(os.environ["TEMP"]) / (container + ".json")
    auth = json.loads(credential.read_text(encoding="utf-8-sig"))
    if auth.get("database") != database or len(auth.get("password", "")) < 24:
        raise RuntimeError("Preview credential identity mismatch")
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    results = []

    def request(path, params):
        data = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params, "id": 1}).encode()
        response = json.loads(opener.open(Request(url + path, data=data, headers={"Content-Type": "application/json"}), timeout=45).read())
        if response.get("error"):
            raise RPCError(response["error"].get("data", {}))
        return response.get("result")

    def call(model, method, args=None, **kwargs):
        return request("/web/dataset/call_kw/" + model + "/" + method,
                       {"model": model, "method": method, "args": args or [], "kwargs": kwargs})

    def read(model, ids, names):
        return call(model, "read", [ids], fields=names)

    def passed(name, **detail):
        results.append({"case": name, "status": "passed", **detail})
        print("OCT_HTTP_CASE=" + json.dumps(results[-1], sort_keys=True), flush=True)

    def refused(name, operation, kinds=("UserError", "ValidationError", "AccessError")):
        try:
            operation()
        except RPCError as error:
            if error.kind.rsplit(".", 1)[-1] not in kinds:
                raise
            passed(name, refusal=error.kind)
            return
        raise AssertionError(name + " unexpectedly succeeded")

    def allocation(order):
        pickings = read("stock.picking", order["picking_ids"], ["move_ids", "state"])
        moves = [mid for p in pickings if p["state"] not in ("done", "cancel") for mid in p["move_ids"]]
        return sum(m["quantity"] for m in read("stock.move", moves, ["quantity"])) if moves else 0

    session = request("/web/session/authenticate", {"db": database, "login": auth["login"], "password": auth["password"]})
    auth = None
    if not session or not session.get("uid"):
        raise AssertionError("Authentication failed")
    passed("authenticated_synthetic_coordinator", uid=session["uid"])
    orders = call("sale.order", "search_read", [[("oct_campaign_pool_id", "!=", False)]],
                  fields=["name", "order_line", "picking_ids", "oct_campaign_policy", "oct_dispatch_promise_ids"], order="name")
    assert len(orders) == 3
    # Seed confirms C/B/A in reverse order, so SO names do not identify A/B/C.
    by_quantity = {sum(line["product_uom_qty"] for line in read("sale.order.line", order["order_line"], ["product_uom_qty"])): order for order in orders}
    assert set(by_quantity) == {200, 600, 100}
    a, b, c = (by_quantity[quantity] for quantity in (200, 600, 100))
    orders = [a, b, c]
    pool = call("oct.campaign.pool", "search_read", [[]], fields=["warehouse_id", "product_ids", "location_id", "responsible_id"])
    assert len(pool) == 1
    pool = pool[0]
    original = [allocation(o) for o in orders]
    assert original == [200, 300, 0], original
    passed("initial_date_priority_over_reverse_confirmation", allocation=original)
    for model, needle in [("sale.order", "oct_campaign_policy"), ("oct.dispatch.promise", "original_date"),
                          ("oct.dispatch.wizard", "response_evidence"), ("oct.campaign.pool", "product_ids")]:
        view = call(model, "get_view", view_type="form")
        assert needle in view["arch"]
    passed("resolved_sales_promise_response_and_pool_forms", browser_render=False)
    refused("confirmed_campaign_policy_is_frozen", lambda: call("sale.order", "write", [[a["id"]], {"oct_campaign_policy": "corporate"}]))
    refused("open_campaign_pool_cannot_be_archived", lambda: call("oct.campaign.pool", "write", [[pool["id"]], {"active": False}]))
    promise_id = c["oct_dispatch_promise_ids"][0]
    refused("proposal_requires_reason", lambda: call("oct.dispatch.promise", "propose", [[promise_id], "2026-12-13", " "]))
    proposal = call("oct.dispatch.promise", "propose", [[promise_id], "2026-12-13", "Synthetic HTTP proposal"])
    call("oct.dispatch.promise", "set_estimate", [[promise_id], "2026-12-12"])
    assert [allocation(o) for o in orders] == original
    passed("pending_proposal_and_estimate_do_not_reallocate")
    refused("customer_response_requires_evidence", lambda: call("oct.dispatch.proposal", "respond", [[proposal], "accepted", "Synthetic Customer", "phone", "2026-10-15 12:00:00", " "]))
    assert read("oct.dispatch.proposal", [proposal], ["state"])[0]["state"] == "pending"
    assert call("oct.dispatch.proposal", "respond", [[proposal], "rejected", "Synthetic Customer", "phone", "2026-10-15 12:00:00", "Synthetic rejection"])
    assert [allocation(o) for o in orders] == original
    passed("rejection_keeps_current_date_and_allocation")
    proposal = call("oct.dispatch.promise", "propose", [[promise_id], "2026-12-13", "Synthetic accepted earlier dispatch"])
    assert call("oct.dispatch.proposal", "respond", [[proposal], "accepted", "Synthetic Customer", "phone", "2026-10-15 12:01:00", "Synthetic acceptance"])
    promise = read("oct.dispatch.promise", [promise_id], ["original_date", "current_date", "estimate_date"])[0]
    assert promise == {"id": promise_id, "original_date": "2026-12-17", "current_date": "2026-12-13", "estimate_date": "2026-12-12"}
    assert [allocation(o) for o in orders] == [200, 200, 100]
    passed("accepted_date_reallocates_and_preserves_history", allocation=[200, 200, 100])
    refused("final_response_cannot_be_overwritten", lambda: call("oct.dispatch.proposal", "respond", [[proposal], "rejected", "Synthetic Customer", "phone", "2026-10-15 12:01:00", "Conflicting retry"]))

    def prepare(order, quantity):
        picking = read("stock.picking", order["picking_ids"], ["move_ids"])[0]
        call("stock.move", "write", [picking["move_ids"], {"quantity": quantity, "picked": True}])
        return order["picking_ids"][0]

    picking_a = prepare(a, 100)
    refused("individual_partial_dispatch_refused", lambda: call("stock.picking", "button_validate", [[picking_a]]))
    assert read("stock.picking", [picking_a], ["state"])[0]["state"] != "done"
    # Prepared whole moves are protected. Explicitly unprepare and recheck
    # before increasing the saved quantity to the full individual order.
    move_ids = read("stock.picking", [picking_a], ["move_ids"])[0]["move_ids"]
    call("stock.move", "write", [move_ids, {"picked": False}])
    call("stock.picking", "action_assign", [[picking_a]])
    assert allocation(a) == 200
    passed("explicit_unprepare_and_recheck_restores_complete_allocation")
    picking_a = prepare(a, 200)
    call("stock.picking", "button_validate", [[picking_a]])
    assert read("stock.picking", [picking_a], ["state"])[0]["state"] == "done"
    passed("individual_complete_dispatch_succeeds", quantity=200)
    picking_c = prepare(c, 100)
    call("stock.picking", "button_validate", [[picking_c]])
    assert read("stock.picking", [picking_c], ["state"])[0]["state"] == "done"
    passed("earlier_reprioritized_individual_dispatch_succeeds", quantity=100)
    refused("saved_preparation_cannot_exceed_allocation", lambda: prepare(b, 300))
    assert allocation(b) == 200
    picking_b = prepare(b, 50)
    call("stock.picking", "button_validate", [[picking_b]])
    assert read("stock.picking", [picking_b], ["state"])[0]["state"] == "done"
    backorders = call("stock.picking", "search_read", [[("backorder_id", "=", picking_b)]], fields=["move_ids", "state"])
    assert len(backorders) == 1
    moves = read("stock.move", backorders[0]["move_ids"], ["product_uom_qty", "quantity"])
    assert sum(m["product_uom_qty"] for m in moves) == 550
    assert sum(m["quantity"] for m in moves) == 150
    passed("corporate_partial_preserves_backorder", shipped=50, remaining=550, reserved=150)
    promise_b = b["oct_dispatch_promise_ids"][0]
    stale = call("oct.dispatch.promise", "propose", [[promise_b], "2026-12-14", "Synthetic stale-scope proposal"])
    call("sale.order.line", "write", [b["order_line"], {"product_uom_qty": 601}])
    assert not call("oct.dispatch.proposal", "respond", [[stale], "accepted", "Synthetic Customer", "phone", "2026-10-15 12:02:00", "Synthetic stale acceptance"])
    stale_record = read("oct.dispatch.proposal", [stale], ["state", "applied", "response_decision"])[0]
    assert stale_record["state"] == "stale" and not stale_record["applied"] and stale_record["response_decision"] == "accepted"
    assert read("oct.dispatch.promise", [promise_b], ["current_date"])[0]["current_date"] == "2026-12-16"
    passed("stale_acceptance_retained_without_date_change")

    item = call("operations.control.item", "create", [{"name": "Synthetic HTTP lifecycle probe", "deadline": "2020-01-01", "next_action": "Synthetic follow-up"}])
    selections = call("operations.control.item", "fields_get", [["area", "impact", "priority"]], attributes=["selection"])
    for field in ("area", "impact", "priority"):
        choices = [choice[0] for choice in selections[field]["selection"]]
        assert choices
        for choice in choices:
            call("operations.control.item", "write", [[item], {field: choice}])
            assert read("operations.control.item", [item], [field])[0][field] == choice
        passed("control_item_all_" + field + "_choices", count=len(choices))
    for view_type in ("kanban", "list", "calendar", "graph", "pivot"):
        assert call("operations.control.item", "get_view", view_type=view_type)["arch"]
    passed("control_item_overview_list_calendar_graph_pivot_server_views", browser_render=False)
    states = ["new", "in_progress", "waiting_responsible", "waiting_information", "waiting_third_party", "blocked", "resolved", "closed"]
    for state in states:
        call("operations.control.item", "write", [[item], {"state": state}])
        record = read("operations.control.item", [item], ["state", "is_overdue", "reference"])[0]
        assert record["state"] == state and record["is_overdue"] == (state not in ("resolved", "closed"))
        assert record["reference"] != "New"
    call("operations.control.item", "unlink", [[item]])
    passed("control_item_all_eight_states_overdue_and_manager_delete")

    # Native warehouse setup requires Settings administration. Do not grant it
    # to this operational actor merely to exercise a configuration test.
    refused("operational_actor_cannot_create_warehouse_settings",
            lambda: call("stock.warehouse", "create", [{"name": "Synthetic HTTP Configuration", "code": "HVAL"}]), kinds=("AccessError",))
    # Observe deletion separately rather than inventing an unapproved rule.
    # The fixture is disposable and this is its final operation.
    try:
        call("oct.campaign.pool", "unlink", [[pool["id"]]])
    except RPCError as error:
        observation = {"case": "linked_pool_deletion", "status": "observation", "allowed": False, "refusal": error.kind}
    else:
        linked = read("sale.order", [b["id"]], ["oct_campaign_pool_id", "oct_campaign_policy"])[0]
        observation = {"case": "linked_pool_deletion", "status": "observation", "allowed": True,
                       "remaining_order_pool": linked["oct_campaign_pool_id"], "remaining_order_policy": linked["oct_campaign_policy"]}
        refused("missing_deleted_pool_dispatch_fails_closed",
                lambda: call("stock.picking", "button_validate", [[backorders[0]["id"]]]), kinds=("UserError",))
    print("OCT_HTTP_OBSERVATION=" + json.dumps(observation, sort_keys=True), flush=True)
    print("OCT_HTTP_RESULT=" + json.dumps({"database": database, "status": "passed", "cases": results, "observations": [observation],
          "limitations": ["HTTP JSON-RPC and resolved server forms, not browser rendering", "Combined synthetic coordinator/stock/operations-manager actor", "No external customer messages or production data", "All fixtures removed with the owned preview database"]}, sort_keys=True))


if __name__ == "__main__":
    main()
