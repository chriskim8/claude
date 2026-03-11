"""Analyze residency customer signal themes from the Customer Signals tab."""
from __future__ import annotations

import os
import sys
import importlib.util as _ilu
from collections import Counter, defaultdict

_GOOGLE = os.path.expanduser("~/google-services")

def _load_pkg(pkg_dir, module_names):
    mods = {}
    for name in module_names:
        path = os.path.join(pkg_dir, f"{name}.py")
        spec = _ilu.spec_from_file_location(f"_{pkg_dir}_{name}", path,
                                            submodule_search_locations=[])
        mod = _ilu.module_from_spec(spec)
        sys.modules[f"_{pkg_dir}_{name}"] = mod
        mods[name] = (spec, mod)
    loaded = {}
    for name, (spec, mod) in mods.items():
        sys.modules["config"] = mods.get("config", (None, None))[1]
        spec.loader.exec_module(mod)
        loaded[name] = mod
    sys.modules.pop("config", None)
    return loaded

_g = _load_pkg(_GOOGLE, ["config", "google_client"])
get_sheets_service = _g["google_client"].get_sheets_service

SPREADSHEET_ID = "1XZA9qrHAAq3dBybhe4oD8O5gkXpg5e3Rmb87fmVQc2E"

# Keywords to surface specific sub-themes within tickets
KEYWORD_PATTERNS = {
    "viewer / schedule access":    ["viewer", "view schedule", "can't see", "cannot see", "access"],
    "block / rotation assignment": ["block", "rotation", "assign", "split"],
    "call schedule":               ["call", "on-call", "oncall"],
    "academic year / training":    ["academic year", "pgy", "training level", "graduation", "intern", "resident"],
    "migration / import":          ["migrat", "import", "classic", "transfer", "convert", "csv"],
    "MedHub / NI integration":     ["medhub", "new innov", "integration", "export", "sync"],
    "notifications / alerts":      ["notif", "email", "alert", "remind", "message"],
    "clinic":                      ["clinic", "continuity"],
    "duty hours / ACGME":          ["duty hour", "acgme", "hour limit", "80 hour"],
    "tally / reporting":           ["tally", "report", "count", "summary"],
    "login / account access":      ["login", "password", "account", "sign in", "sso", "auth"],
    "performance / bugs":          ["slow", "bug", "error", "crash", "not working", "broken", "issue"],
}


def read_signals(sheets_svc):
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="'Customer Signals'!A3:H2000",  # skip title + header rows
    ).execute()
    return result.get("values", [])


def analyze(rows):
    theme_counts = Counter()
    theme_rows = defaultdict(list)
    source_counts = Counter()
    keyword_counts = Counter()
    status_counts = Counter()

    for row in rows:
        if not row or len(row) < 3:
            continue
        source  = row[0] if len(row) > 0 else ""
        title   = row[1] if len(row) > 1 else ""
        theme   = row[2] if len(row) > 2 else "Other"
        votes   = row[3] if len(row) > 3 else ""
        status  = row[4] if len(row) > 4 else ""
        date    = row[5] if len(row) > 5 else ""
        notes   = row[7] if len(row) > 7 else ""

        theme_counts[theme] += 1
        source_counts[source] += 1
        status_counts[status] += 1
        theme_rows[theme].append({
            "source": source, "title": title, "votes": votes,
            "status": status, "date": date, "notes": notes[:200],
        })

        # keyword sub-theme matching
        text = (title + " " + notes).lower()
        for kw_theme, kw_list in KEYWORD_PATTERNS.items():
            if any(k in text for k in kw_list):
                keyword_counts[kw_theme] += 1

    total = sum(theme_counts.values())
    zd_total = source_counts.get("Zendesk", 0)
    ca_total = source_counts.get("Canny", 0)

    print(f"\n{'='*64}")
    print(f"CUSTOMER SIGNAL ANALYSIS — Residency (Amion Brand, Last 12 Mo)")
    print(f"{'='*64}")
    print(f"Total signals: {total}  |  Zendesk: {zd_total}  |  Canny: {ca_total}")
    print(f"Ticket statuses: " + ", ".join(f"{s}={c}" for s, c in sorted(status_counts.items(), key=lambda x: -x[1])))

    print(f"\n{'─'*64}")
    print(f"THEME BREAKDOWN (auto-classified by keyword)")
    print(f"{'─'*64}")
    print(f"  {'Theme':<28} {'Count':>6}  {'%':>5}  {'Top Signal'}")
    print(f"  {'─'*28}  {'─'*6}  {'─'*5}  {'─'*28}")
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        sample_title = ""
        for r in theme_rows[theme]:
            if r["title"]:
                sample_title = r["title"][:40]
                break
        print(f"  {theme:<28} {count:>6}  {pct:>4.1f}%  \"{sample_title}\"")

    print(f"\n{'─'*64}")
    print(f"KEYWORD SUB-THEME HITS (across all signals)")
    print(f"{'─'*64}")
    print(f"  {'Sub-theme':<35} {'Hits':>6}")
    print(f"  {'─'*35}  {'─'*6}")
    for kw, count in sorted(keyword_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count // 5, 30)
        print(f"  {kw:<35} {count:>6}  {bar}")

    print(f"\n{'─'*64}")
    print(f"TOP 5 SIGNALS PER THEME (by recency)")
    print(f"{'─'*64}")
    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        tickets = theme_rows[theme]
        recent = sorted(tickets, key=lambda t: t.get("date", ""), reverse=True)[:5]
        print(f"\n  [{theme}] — {count} signals")
        for t in recent:
            src = f"[{t['source']}]"
            title = (t["title"] or "")[:65]
            print(f"    {src:<10} {title}")
            if t["notes"]:
                snippet = t["notes"][:90].replace("\n", " ")
                print(f"               ↳ {snippet}")


if __name__ == "__main__":
    svc = get_sheets_service()
    rows = read_signals(svc)
    analyze(rows)
