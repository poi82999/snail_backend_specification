"""Cross-reference verification: OWNER_SECTION_MAP vs backend spec data."""
import sys
sys.path.insert(0, "tools")
from build_owner_webapp_index import load_backend_data, OWNER_SECTION_MAP, SCREEN_PLAYBOOKS

backend = load_backend_data()

# Collect ALL registered APIs and entities across sections
registered_apis = set()
registered_fields = set()
for sec in OWNER_SECTION_MAP:
    for group, endpoints in sec.get("apis", {}).items():
        for ep in endpoints:
            registered_apis.add(ep)
    for entity, fields in sec.get("entities", {}).items():
        for f in fields:
            registered_fields.add(f"{entity}.{f}")

# ALL APIs in backend
all_apis = set()
owner_apis = set()
for group, gdata in backend["apis"].items():
    for ep in gdata["items"]:
        all_apis.add(ep)
        if "/owner/" in ep:
            owner_apis.add(ep)

# ALL fields
all_fields = set()
for entity, edata in backend["entities"].items():
    for f in edata["fields"]:
        all_fields.add(f"{entity}.{f}")

issues = []

# 1. Owner APIs not in any section
missing_owner_apis = owner_apis - registered_apis
for api in sorted(missing_owner_apis):
    issues.append(("CRITICAL", "API_COVERAGE", "-", f"Owner API {api} exists in backend but NOT mapped to any section"))

# 2. Registered APIs not in backend (phantom)
phantom_apis = registered_apis - all_apis
for api in sorted(phantom_apis):
    issues.append(("CRITICAL", "PHANTOM_API", "-", f"API {api} listed in section mapping but NOT found in backend spec"))

# 3. Per-section field coverage
for sec in OWNER_SECTION_MAP:
    sid = sec["id"]
    title = sec["title"]
    sec_fields = set()
    for entity, fields in sec.get("entities", {}).items():
        for f in fields:
            key = f"{entity}.{f}"
            sec_fields.add(key)
            if key not in all_fields:
                issues.append(("CRITICAL", "PHANTOM_FIELD", sid, f"Field {key} listed but NOT in backend spec"))

# 4. Key fields missing from sections
key_entity_map = {
    "Owner": "1",
    "Shop": "2",
    "Designer": "3",
    "Design": "4",
    "DesignImage": "4",
    "Reservation": "5",
    "Review": "6",
    "OwnerNotification": "9",
}
for entity, expected_section in key_entity_map.items():
    edata = backend["entities"].get(entity, {"fields": {}})
    for f in edata["fields"]:
        key = f"{entity}.{f}"
        if key not in registered_fields:
            # Skip auto-generated IDs and timestamps
            if f in ("created_at", "owner_id", "shop_id", "design_id", "user_id"):
                continue
            issues.append(("WARNING", "MISSING_FIELD", expected_section, f"Field {key} exists in backend but not registered in section {expected_section}"))

# 5. Playbook verification - check API endpoints in ui_events
for sid, playbook in SCREEN_PLAYBOOKS.items():
    for trigger, api, success, failure in playbook.get("ui_events", []):
        # Extract API endpoint from the description
        api_parts = api.strip()
        # Check if it looks like a real API path
        if api_parts.startswith(("POST ", "GET ", "PATCH ", "DELETE ", "PUT ")):
            method_ep = api_parts.split(" -> ")[0].strip() if " -> " in api_parts else api_parts
            if method_ep not in all_apis:
                # May have template params - try matching
                found = False
                for real_api in all_apis:
                    if method_ep.replace("{id}", "{design_id}") == real_api or method_ep == real_api:
                        found = True
                        break
                if not found:
                    issues.append(("WARNING", "PLAYBOOK_API", sid, f"ui_event API '{method_ep}' may not match backend (trigger: {trigger})"))

# 6. Check Reservation statuses in playbook vs spec
spec_statuses = {"pending", "payment_pending", "confirmed", "completed", "no_show", "cancelled_by_user", "cancelled_by_shop", "rejected"}
playbook_5 = SCREEN_PLAYBOOKS.get("5", {})
playbook_states = playbook_5.get("states", [])
mentioned_statuses = set()
for state_desc in playbook_states:
    for st in spec_statuses:
        if st in state_desc:
            mentioned_statuses.add(st)
missing_statuses = spec_statuses - mentioned_statuses
if missing_statuses:
    issues.append(("WARNING", "STATUS_COVERAGE", "5", f"Reservation statuses not mentioned in playbook states: {missing_statuses}"))

# Print report
print("=" * 80)
print("VERIFICATION REPORT: OWNER_SECTION_MAP vs Backend Spec")
print("=" * 80)

by_severity = {"CRITICAL": [], "WARNING": [], "INFO": []}
for severity, category, section, desc in issues:
    by_severity[severity].append((category, section, desc))

for sev in ("CRITICAL", "WARNING", "INFO"):
    items = by_severity[sev]
    if items:
        print(f"\n{'='*3} {sev} ({len(items)}) {'='*3}")
        for cat, sec, desc in items:
            print(f"  [{cat}] Section {sec}: {desc}")

print(f"\n{'='*80}")
print(f"Total issues: CRITICAL={len(by_severity['CRITICAL'])}, WARNING={len(by_severity['WARNING'])}, INFO={len(by_severity['INFO'])}")
print(f"Registered APIs: {len(registered_apis)}, Backend APIs: {len(all_apis)}, Owner APIs: {len(owner_apis)}")
print(f"Registered Fields: {len(registered_fields)}, Backend Fields: {len(all_fields)}")
