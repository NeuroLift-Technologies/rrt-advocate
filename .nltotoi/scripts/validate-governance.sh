#!/usr/bin/env bash
# validate-governance.sh
# Validates ORG-DEV-OTOI-1.0.0 compliance for NeuroLift-Technologies/rrt-advocate
# Usage: bash .nltotoi/scripts/validate-governance.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
PASS=0
FAIL=0
WARN=0

check_file() {
  local path="$1"
  local label="$2"
  local level="${3:-required}"
  if [ -f "$REPO_ROOT/$path" ] || [ -d "$REPO_ROOT/$path" ]; then
    echo "  ✅ $label ($path)"
    PASS=$((PASS + 1))
  else
    if [ "$level" = "required" ]; then
      echo "  ❌ MISSING [REQUIRED]: $label ($path)"
      FAIL=$((FAIL + 1))
    else
      echo "  ⚠️  MISSING [RECOMMENDED]: $label ($path)"
      WARN=$((WARN + 1))
    fi
  fi
}

echo ""
echo "============================================="
echo "  NLT Governance Validator — ORG-DEV-OTOI-1.0.0"
echo "  Repository: NeuroLift-Technologies/rrt-advocate"
echo "============================================="
echo ""

echo "--- Critical Files ---"
check_file "CLAUDE.md"                                          "AI assistant guide"
check_file "AGENTS.md"                                         "Agent coordination protocol"
check_file "docs/active-threads.md"                            "Active work state tracker"
check_file "docs/agent-log/README.md"                          "Agent log directory"
check_file "docs/agent-log/registrations"                      "Registrations directory"
check_file "docs/agent-log/handoffs"                           "Handoffs directory"
check_file "GEMINI_TOPOGRAPHY.py"                              "Repo navigation guide"

echo ""
echo "--- Template Files ---"
check_file "templates/agent-registration.json"                 "Agent registration template"
check_file "templates/handoff-record.json"                     "Handoff record template"
check_file "templates/escalation.md"                           "Escalation template"
check_file "templates/intent-log.md"                           "Intent log template"

echo ""
echo "--- GitHub Issue Forms ---"
check_file ".github/ISSUE_TEMPLATE/agent-escalation.md"        "Agent escalation form"
check_file ".github/ISSUE_TEMPLATE/governance-proposal.md"     "Governance proposal form"

echo ""
echo "--- Recommended Files ---"
check_file ".nltotoi/index/governance-files.md"                "Governance file index" recommended
check_file ".nltotoi/scripts/validate-governance.sh"           "This validation script" recommended

echo ""
echo "============================================="
echo "  Results: $PASS passed | $FAIL failed | $WARN warnings"
echo "============================================="
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "  ⛔ GOVERNANCE CHECK FAILED — $FAIL required file(s) missing."
  echo "  File an escalation or add missing files before committing."
  exit 1
else
  echo "  ✅ All required governance files present."
  if [ "$WARN" -gt 0 ]; then
    echo "  ⚠️  $WARN recommended file(s) missing (non-blocking)."
  fi
  exit 0
fi
