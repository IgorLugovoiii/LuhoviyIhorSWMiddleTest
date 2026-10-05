# МКР — Варіант 1 (N = 20)

## Завдання 1. RDF-граф рейсів

Дані: `python gen_data.py --seed 20` → `flights.csv` (18 рядків), `params.json`
(`budget_threshold_eur = 89`, `long_flight_min = 210`).

Побудова графа:

```
python build_graph.py flights.csv params.json graph.ttl
```

Результат: `graph.ttl` — 16 рейсів (2 дублікати злиті), 277 тріплів.

## Завдання 2. SPARQL-запити до Wikidata

Параметри: 20 mod 6 = **2** → клас **Q483110** (стадіон), країна **Q36** (Польща),
властивість **P1083** (місткість), поріг **10000**.

Запуск: `python run_queries.py` → `q1.csv`, `q2.csv`, `q3.csv`, `meta.json`, `ANSWERS.md`.

### Запит 1 — стадіони з місткістю > 10000 та їхній сайт

Перший рядок результату (`q1.csv`):

| item | itemLabel | value | website |
|---|---|---|---|
| wd:Q7596298 | Edmund Szyc Stadium | 60000 | — |

```sparql
# Q1. Стадіони (Q483110) у Польщі (Q36) з місткістю (P1083) > 10000 + офіційний сайт
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?item ?itemLabel ?value ?website WHERE {
  {
    SELECT ?item (MAX(?v) AS ?value) (SAMPLE(?w) AS ?website) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q36 ;
            wdt:P1083 ?v .
      OPTIONAL { ?item wdt:P856 ?w . }
    }
    GROUP BY ?item
  }
  FILTER(?value > 10000)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?value) ?item
LIMIT 20
```

### Запит 2 — регіони з найбільшою кількістю стадіонів (≥ 3)

Перший рядок результату (`q2.csv`):

| region | regionLabel | cnt |
|---|---|---|
| wd:Q31487 | Kraków | 11 |

```sparql
# Q2. Регіони Польщі (Q36) з найбільшою кількістю стадіонів (Q483110), щонайменше 3
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?region ?regionLabel ?cnt WHERE {
  {
    SELECT ?region (COUNT(DISTINCT ?item) AS ?cnt) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q36 ;
            wdt:P131 ?region .
    }
    GROUP BY ?region
    HAVING (COUNT(DISTINCT ?item) >= 3)
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?cnt) ?region
LIMIT 10
```

### Запит 3 — стадіони в регіонах із найбільшим населенням

Перший рядок результату (`q3.csv`):

| item | itemLabel | region | regionLabel | population |
|---|---|---|---|---|
| wd:Q135274726 | Q135274726 (без англ. назви) | wd:Q54181 | Silesian Voivodeship | 4617000 |

```sparql
# Q3. Стадіони (Q483110) у Польщі (Q36) та населення (P1082) їхнього регіону (P131)
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?item ?itemLabel ?region ?regionLabel ?population WHERE {
  {
    SELECT ?item ?region (MAX(?p) AS ?population) WHERE {
      ?item wdt:P31 wd:Q483110 ;
            wdt:P17 wd:Q36 ;
            wdt:P131 ?region .
      ?region wdt:P1082 ?p .
    }
    GROUP BY ?item ?region
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?population) ?item
LIMIT 10
```
