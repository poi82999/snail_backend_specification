"""Cross-reference verification: LLM Pipeline mapping vs backend spec data."""
import sys
sys.path.insert(0, "tools")
from build_owner_webapp_index import load_backend_data
from build_llm_pipeline_index import (
    PIPELINE_MAP, LLM_STEP_PLAYBOOKS, load_llm_spec,
    EASY_FIELD_EXPLANATIONS, EASY_CONTRACT_FIELD_EXPLANATIONS,
    EASY_API_EXPLANATIONS, STEP_PLAIN_LANGUAGE,
)

backend = load_backend_data()
llm_spec = load_llm_spec()

issues = []

# 1. Entity fields
for step in PIPELINE_MAP:
    for entity, fields in step.get("entities", {}).items():
        edata = backend["entities"].get(entity, {"fields": {}})
        for f in fields:
            if f not in edata["fields"]:
                issues.append(("CRITICAL", "PHANTOM_FIELD", step["id"], f"{entity}.{f} NOT in backend"))

# 2. APIs
for step in PIPELINE_MAP:
    for group, endpoints in step.get("apis", {}).items():
        gdata = backend["apis"].get(group)
        if not gdata:
            issues.append(("CRITICAL", "PHANTOM_GROUP", step["id"], f"API group {group} NOT in backend"))
            continue
        for ep in endpoints:
            if ep not in gdata["items"]:
                issues.append(("CRITICAL", "PHANTOM_API", step["id"], f"API {ep} NOT in backend"))

# 3. Error codes
for code, meaning, msg in llm_spec.get("error_codes", []):
    if not code or not meaning:
        issues.append(("WARNING", "ERROR_CODE", "-", f"Incomplete error code: {code}"))

# 4. Standard tags
tags = llm_spec.get("standard_tags", {})
if not tags:
    issues.append(("CRITICAL", "TAGS", "-", "No standard tags defined"))
else:
    for cat, values in tags.items():
        if not values:
            issues.append(("WARNING", "TAGS", "-", f"Empty tag category: {cat}"))

# 5. Easy field explanations
for step in PIPELINE_MAP:
    for entity, fields in step.get("entities", {}).items():
        for f in fields:
            if f not in EASY_FIELD_EXPLANATIONS:
                issues.append(("INFO", "EASY_FIELD", step["id"], f"No easy explanation for {entity}.{f}"))

# 6. Contract field explanations
for key in ("transform", "classify"):
    contract = llm_spec.get(key, {})
    for f in contract.get("request_fields", []) + contract.get("response_fields", []):
        if f not in EASY_CONTRACT_FIELD_EXPLANATIONS:
            issues.append(("WARNING", "CONTRACT_EXPLAIN", key, f"No easy explanation for contract field: {f}"))

# 7. Playbook completeness
for step_id, playbook in LLM_STEP_PLAYBOOKS.items():
    if not playbook.get("qa"):
        issues.append(("WARNING", "QA_MISSING", step_id, "No QA checklist"))
    if not playbook.get("call_order"):
        issues.append(("WARNING", "CALLORDER_MISSING", step_id, "No call_order"))

# 8. Every step has a playbook and plain language
for step in PIPELINE_MAP:
    if step["id"] not in LLM_STEP_PLAYBOOKS:
        issues.append(("CRITICAL", "PLAYBOOK_MISSING", step["id"], "No playbook for step"))
    if step["id"] not in STEP_PLAIN_LANGUAGE:
        issues.append(("WARNING", "PLAIN_LANG", step["id"], "No plain language explanation"))

print("=" * 80)
print("VERIFICATION REPORT: LLM PIPELINE")
print("=" * 80)

by_sev = {"CRITICAL": [], "WARNING": [], "INFO": []}
for sev, cat, sid, desc in issues:
    by_sev[sev].append((cat, sid, desc))

for sev in ("CRITICAL", "WARNING", "INFO"):
    items = by_sev[sev]
    if items:
        print(f"\n=== {sev} ({len(items)}) ===")
        for cat, sid, desc in items:
            print(f"  [{cat}] Step {sid}: {desc}")

crit = len(by_sev["CRITICAL"])
warn = len(by_sev["WARNING"])
info = len(by_sev["INFO"])
print(f"\nTotal: CRITICAL={crit}, WARNING={warn}, INFO={info}")
print(f"Pipeline steps: {len(PIPELINE_MAP)}")
print(f"Playbooks: {len(LLM_STEP_PLAYBOOKS)}")
print(f"Error codes: {len(llm_spec.get('error_codes', []))}")
print(f"Tag categories: {len(tags)}")
print(f"Contract fields explained: {len(EASY_CONTRACT_FIELD_EXPLANATIONS)}")
