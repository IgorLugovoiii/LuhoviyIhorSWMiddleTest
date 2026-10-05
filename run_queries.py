"""МКР, Варіант 1, Завдання 2 (N = 20 -> залишок 2: стадіони, Польща, P1083, поріг 10000).
Запуск: python run_queries.py
"""
import csv
import json
from datetime import datetime

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "mkr1/1.0", "Accept": "application/sparql-results+json"}
THRESHOLD = 10000

COLUMNS = {
    "q1": ["item", "itemLabel", "value", "website"],
    "q2": ["region", "regionLabel", "cnt"],
    "q3": ["item", "itemLabel", "region", "regionLabel", "population"],
}


def run(query):
    r = requests.get(ENDPOINT, params={"query": query, "format": "json"},
                     headers=HEADERS, timeout=120)
    r.raise_for_status()
    data = r.json()
    return [{k: v["value"] for k, v in b.items()} for b in data["results"]["bindings"]]


def save_csv(name, rows):
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS[name], extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in COLUMNS[name]})


def read_query(name):
    with open(f"{name}.rq", encoding="utf-8") as f:
        return f.read()


def main():
    results = {}
    note = None
    for name in COLUMNS:
        query = read_query(name)
        rows = run(query)
        if name == "q1" and len(rows) < 5:
            new_t = THRESHOLD // 2
            query = query.replace(f"> {THRESHOLD})", f"> {new_t})")
            with open("q1.rq", "w", encoding="utf-8") as f:
                f.write(query)
            rows = run(query)
            note = f"Примітка: Q1 повернув менше 5 рядків, поріг зменшено вдвічі до {new_t}."
        save_csv(name, rows)
        results[name] = rows
        print(f"{name}.csv: {len(rows)} рядків")

    with open("meta.json", "w", encoding="utf-8") as f:
        json.dump({"retrieved_at": datetime.now().isoformat(timespec="seconds")}, f,
                  ensure_ascii=False, indent=2)

    q1, q2, q3 = results["q1"], results["q2"], results["q3"]
    lines = [
        f"Q1: {q1[0]['itemLabel']} — {q1[0]['value']}" if q1 else "Q1: немає результатів",
        f"Q2: {q2[0]['regionLabel']} — {q2[0]['cnt']}" if q2 else "Q2: немає результатів",
        f"Q3: {q3[0]['population']}" if q3 else "Q3: немає результатів",
    ]
    if note:
        lines.append(note)
    with open("ANSWERS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
