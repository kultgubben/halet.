#!/usr/bin/env python3
"""Merge the four research JSONs into one normalized DATA blob and inject into the HTML template."""
import json, re, unicodedata, sys, os

SP = os.path.dirname(os.path.abspath(__file__))
route = json.load(open(f"{SP}/route.json"))
results = json.load(open(f"{SP}/results.json"))
standings = json.load(open(f"{SP}/standings.json"))
startlist = json.load(open(f"{SP}/startlist.json"))

def slug(s):
    s = s.replace("æ", "ae").replace("ø", "o").replace("ß", "ss").replace("Æ", "AE").replace("Ø", "O")
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"[^a-z0-9]", "", s.encode("ascii", "ignore").decode().lower())

# ---- team canonicalization: canonical id = startlist short name ----
teams = startlist["teams"]
team_by_slug = {}
for t in teams:
    for key in (t["name"], t["short"]):
        team_by_slug[slug(key)] = t["short"]

ALIASES = {
    "teamvismaleaseabike": "Visma", "vismaleaseabike": "Visma",
    "netcompanyineos": "Ineos", "ineosgrenadiers": "Ineos", "netcompanyineosgrenadiers": "Ineos",
    "uaeteamemiratesxrg": "UAE", "uaeteamemirates": "UAE",
    "redbullborahansgrohe": "Red Bull",
    "lidltrek": "Lidl-Trek",
    "decathloncmacgmteam": "Decathlon", "decathloncmacgm": "Decathlon",
    "efeducationeasypost": "EF",
    "teamjaycoalula": "Jayco", "jaycoalula": "Jayco",
    "soudalquickstep": "Soudal",
    "pinarelloq365procyclingteam": "Q36.5", "pinarelloq365": "Q36.5",
    "lottointermarche": "Lotto",
    "bahrainvictorious": "Bahrain", "teambahrainvictorious": "Bahrain",
    "xdsastanateam": "Astana", "xdsastana": "Astana",
    "teamtotalenergies": "TotalEnergies", "totalenergies": "TotalEnergies",
    "cajaruralsegurosrga": "Caja Rural",
    "unoxmobility": "Uno-X",
    "nsncyclingteam": "NSN",
    "groupamafdjunited": "Groupama",
    "alpecinpremiertech": "Alpecin",
    "movistarteam": "Movistar",
    "tudorprocycling": "Tudor", "tudorprocyclingteam": "Tudor",
    "teampicnicpostnl": "Picnic",
    "cofidis": "Cofidis",
}
team_by_slug.update(ALIASES)

unmatched_teams = set()
def team_short(name):
    if not name: return name
    s = team_by_slug.get(slug(name))
    if s is None:
        unmatched_teams.add(name)
        return name
    return s

# ---- rider canonicalization: prefer startlist spelling (diacritics correct) ----
rider_by_slug = {}
rider_info = {}   # canonical name -> {nat, age, team(short), bib}
for t in teams:
    for r in t["riders"]:
        rider_by_slug[slug(r["name"])] = r["name"]
        # also index "F. Lastname" style and lastname-only? keep full-slug only (safe)
        rider_info[r["name"]] = {"nat": r["nat"], "age": r["age"], "team": t["short"], "bib": r["bib"]}

unmatched_riders = set()
def rider_name(name):
    if not name: return name
    c = rider_by_slug.get(slug(name))
    if c is None:
        unmatched_riders.add(name)
        return name
    return c

# ---- normalize results ----
for st in results["stages"]:
    st["winnerTeam"] = team_short(st["winnerTeam"])
    is_ttt = st["n"] == 1
    if is_ttt:
        st["winner"] = team_short(st["winner"])
    else:
        st["winner"] = rider_name(st["winner"])
    for row in st["top15"]:
        row["team"] = team_short(row["team"])
        row["rider"] = team_short(row["rider"]) if is_ttt else rider_name(row["rider"])
    for j in ("yellow", "green", "polka", "white"):
        st["jerseysAfter"][j] = rider_name(st["jerseysAfter"][j])
    for a in st.get("abandons", []):
        a["rider"] = rider_name(a["rider"]); a["team"] = team_short(a["team"])

# ---- normalize standings ----
for key in ("gc", "points", "kom", "youth"):
    for row in standings[key]:
        row["rider"] = rider_name(row["rider"])
        row["team"] = team_short(row["team"])
        info = rider_info.get(row["rider"])
        if info and "nat" not in row:
            row["nat"] = info["nat"]
for row in standings["teams"]:
    row["team"] = team_short(row["team"])
for a in standings["abandons"]:
    a["rider"] = rider_name(a["rider"]); a["team"] = team_short(a["team"])
for c in standings["combativity"]:
    if c.get("rider"): c["rider"] = rider_name(c["rider"])
    if c.get("team"): c["team"] = team_short(c["team"])

# enrich gc/points/kom/youth rows with nat from startlist
for key in ("points", "kom", "youth"):
    for row in standings[key]:
        info = rider_info.get(row["rider"])
        row["nat"] = info["nat"] if info else row.get("nat")

# ---- derived ----
last = results["lastCompletedStage"]
done = [s for s in route["stages"] if s["n"] <= last]
km_done = round(sum(s["km"] for s in done), 1)
res_by_n = {s["n"]: s for s in results["stages"]}
for s in route["stages"]:
    r = res_by_n.get(s["n"])
    if r:
        s["winner"] = r["winner"]; s["winnerTeam"] = r["winnerTeam"]

# jersey timeline
timeline = [{"n": s["n"], **s["jerseysAfter"]} for s in results["stages"]]

DATA = {
    "meta": {
        "lastStage": last,
        "updated": res_by_n[last]["date"],
        "kmDone": km_done,
        "kmTotal": route["totalDistanceKm"],
        "ridersStarted": sum(len(t["riders"]) for t in teams),
        "ridersLeft": sum(len(t["riders"]) for t in teams) - len(standings["abandons"]),
    },
    "route": route,
    "results": results,
    "standings": standings,
    "startlist": startlist,
    "timeline": timeline,
}

tpl = open(f"{SP}/tdf_template.html", encoding="utf-8").read()
blob = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))
assert "__TDF_DATA__" in tpl
out = tpl.replace("__TDF_DATA__", blob.replace("</", "<\\/"))
dest = "/home/user/halet./tdf-2026.html"
open(dest, "w", encoding="utf-8").write(out)

print("wrote", dest, len(out), "bytes")
print("unmatched teams:", sorted(unmatched_teams) or "none")
print("unmatched riders:", sorted(unmatched_riders) or "none")
