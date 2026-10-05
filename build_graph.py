"""МКР, Варіант 1, Завдання 1.
Запуск: python build_graph.py flights.csv params.json graph.ttl
"""
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

EX = Namespace("http://example.org/mkr/")


def iri(kind, name):
    """ex:<kind>/<name>, пробіли -> _"""
    return EX[f"{kind}/{name.strip().replace(' ', '_')}"]


def parse_date(s):
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Невідомий формат дати: {s!r}")


def parse_note(note):
    """'delay=25;by=AirWatch' -> {'delay': '25', 'by': 'AirWatch'}"""
    out = {}
    for part in (note or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def load_flights(path):
    """Читає CSV, нормалізує й прибирає дублікати (ключ — нормалізований ID)."""
    flights = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            fid = row["flight_id"].strip().upper()
            if fid in flights:
                continue
            price = row["price_eur"].strip()
            flights[fid] = {
                "id": fid,
                "airline": row["airline"].strip(),
                "from_city": row["from_city"].strip().title(),
                "from_country": row["from_country"].strip(),
                "to_city": row["to_city"].strip().title(),
                "to_country": row["to_country"].strip(),
                "date": parse_date(row["dep_date"]),
                "duration": int(row["duration_min"].strip()),
                "price": Decimal(price) if price else None,
                "note": parse_note(row["note"]),
            }
    return list(flights.values())


def add_schema(g):
    for c in ("Flight", "Airline", "City", "Country"):
        g.add((EX[c], RDF.type, RDFS.Class))
    for c in ("BudgetFlight", "LongFlight"):
        g.add((EX[c], RDF.type, RDFS.Class))
        g.add((EX[c], RDFS.subClassOf, EX.Flight))

    obj_props = {
        "operatedBy": (EX.Flight, EX.Airline),
        "departsFrom": (EX.Flight, EX.City),
        "arrivesAt": (EX.Flight, EX.City),
        "locatedIn": (EX.City, EX.Country),
        "reportedBy": (RDF.Statement, RDFS.Resource),
    }
    data_props = {
        "departureDate": (EX.Flight, XSD.date),
        "durationMin": (EX.Flight, XSD.integer),
        "priceEur": (EX.Flight, XSD.decimal),
        "hasDelayMinutes": (EX.Flight, XSD.integer),
        "fromBusyCountry": (EX.Flight, XSD.boolean),
    }
    for name, (dom, rng) in {**obj_props, **data_props}.items():
        g.add((EX[name], RDF.type, RDF.Property))
        g.add((EX[name], RDFS.domain, dom))
        g.add((EX[name], RDFS.range, rng))


def build(flights, params):
    g = Graph()
    g.bind("ex", EX)
    g.bind("xsd", XSD)
    add_schema(g)

    budget = Decimal(str(params["budget_threshold_eur"]))
    long_min = int(params["long_flight_min"])

    dep_count = Counter(fl["from_country"] for fl in flights)

    for fl in flights:
        f = iri("flight", fl["id"])
        airline = iri("airline", fl["airline"])
        city_from = iri("city", fl["from_city"])
        city_to = iri("city", fl["to_city"])

        # Типи
        types = []
        if fl["price"] is not None and fl["price"] <= budget:
            types.append(EX.BudgetFlight)
        if fl["duration"] >= long_min:
            types.append(EX.LongFlight)
        for t in types or [EX.Flight]:
            g.add((f, RDF.type, t))

        # Авіакомпанія
        g.add((f, EX.operatedBy, airline))
        g.add((airline, RDF.type, EX.Airline))
        g.add((airline, RDFS.label, Literal(fl["airline"], lang="en")))

        # Міста й країни
        g.add((f, EX.departsFrom, city_from))
        g.add((f, EX.arrivesAt, city_to))
        for city, cname, country in ((city_from, fl["from_city"], fl["from_country"]),
                                     (city_to, fl["to_city"], fl["to_country"])):
            c = iri("country", country)
            g.add((city, RDF.type, EX.City))
            g.add((city, RDFS.label, Literal(cname, lang="en")))
            g.add((city, EX.locatedIn, c))
            g.add((c, RDF.type, EX.Country))
            g.add((c, RDFS.label, Literal(country, lang="en")))

        # Літерали
        g.add((f, EX.departureDate, Literal(fl["date"].isoformat(), datatype=XSD.date)))
        g.add((f, EX.durationMin, Literal(fl["duration"], datatype=XSD.integer)))
        if fl["price"] is not None:
            g.add((f, EX.priceEur, Literal(str(fl["price"]), datatype=XSD.decimal)))

        # Затримка через реїфікацію
        note = fl["note"]
        if "delay" in note:
            st = EX[f"stmt/{fl['id']}-delay"]
            g.add((st, RDF.type, RDF.Statement))
            g.add((st, RDF.subject, f))
            g.add((st, RDF.predicate, EX.hasDelayMinutes))
            g.add((st, RDF.object, Literal(int(note["delay"]), datatype=XSD.integer)))
            if "by" in note:
                g.add((st, EX.reportedBy, iri("source", note["by"])))

        # Країни з частими вильотами
        if dep_count[fl["from_country"]] >= 2:
            g.add((f, EX.fromBusyCountry, Literal(True, datatype=XSD.boolean)))

    return g


def main():
    if len(sys.argv) != 4:
        print("Використання: python build_graph.py flights.csv params.json graph.ttl")
        sys.exit(1)
    csv_path, params_path, out_path = sys.argv[1:]
    with open(params_path, encoding="utf-8") as f:
        params = json.load(f)
    flights = load_flights(csv_path)
    g = build(flights, params)
    g.serialize(destination=out_path, format="turtle")
    print(f"{out_path}: {len(flights)} рейсів, {len(g)} тріплів")


if __name__ == "__main__":
    main()
