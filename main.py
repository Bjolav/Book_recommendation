import pandas as pd
import random
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import pandas as pd
from rdflib.namespace import RDF, RDFS, OWL
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.recycleview import RecycleView
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from SPARQLWrapper import SPARQLWrapper, JSON

kv = Builder.load_file("my.kv")


class Menu(FloatLayout):
    btn = ObjectProperty(None)
    book = ObjectProperty(None)
    author = ObjectProperty(None)

    def btn(self):
        show_popup(Randomized())

    def btn2(self):
        show_popup(BookSearch)

    def btn3(self):
        show_popup(AuthorSearch)


class Randomized(FloatLayout):
    def __init__(self, **kwargs):
        super(Randomized, self).__init__(**kwargs)
        self.data = [{"text": str(random_book(csv_loader()))}]


class BookSearch(RecycleView, Menu):
    def __init(self, **kwargs):
        super(BookSearch, self).__init__(**kwargs)
        self.data = [{"text": str(x) for x in range(book_search(csv_loader(), Menu.book))}]


class AuthorSearch(RecycleView, Menu):
    def __init(self, **kwargs):
        super(AuthorSearch, self).__init__(**kwargs)
        self.data = [{"text": str(x) for x in range(author_search(csv_loader(), Menu.author))}]


class MyApp(App):
    def build(self):
        return Menu()


def show_popup(instance):
    popupWindow = Popup(title="Result", content=instance)
    popupWindow.open()


def csv_loader():
    # CSV file gets read
    csv_data = pd.read_csv("books.csv", error_bad_lines=False, encoding="utf-8")

    # Deletion of all rows we deem unnecessary
    del csv_data['isbn']
    del csv_data['ratings_count']
    del csv_data['text_reviews_count']

    # Here we change all empty spaces with underscore to make it easier for triple-convertion later
    csv_data = csv_data.replace(' ', '_', regex=True)

    # Here we remove all rows with empty values
    csv_data = csv_data.dropna()

    # Here we remove all rows where the book's page number equals 0
    csv_data = csv_data[csv_data.num_pages != 0]

    # Adds new columns for what series the book is part of, as well as it's positional number in that series,
    # extrapolated from titles that include it
    csv_data[['title', 'series']] = csv_data['title'].str.split('(', 1, expand=True)
    csv_data[['series', 'book_number']] = csv_data['series'].str.split('#', 1, expand=True)

    # Cleans up the rows
    csv_data['book_number'] = csv_data['book_number'].str.strip(')')
    csv_data['title'] = csv_data['title'].str.strip('_')
    csv_data['series'] = csv_data['series'].str.strip('_')
    csv_data['series'] = csv_data['series'].str.strip(')')
    csv_data['publisher;;;'] = csv_data['publisher;;;'].str.strip(';')
    csv_data = csv_data.rename({'publisher;;;': 'publisher'}, axis=1)

    # Books that aren't part of a series gets that established
    csv_data['series'] = csv_data['series'].fillna("Standalone")

    return csv_data


def triples(csv_data):
    g = Graph()
    g.parse("https://www.wikidata.org/wiki/Q571", format="xml")
    schema = Namespace("https://schema.org/")
    g.bind("schema", schema)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    csv_data = csv_data.fillna("unknown")

    for index, row in csv_data.iterrows():
        # Books registered as standalone get assigned the value "1" as it's the one and only book in it's series
        if row["series"] == "Standalone":
            row["book_number"] = "1"

        subject = row['title']
        g.add((URIRef(schema + subject), RDF.type, OWL.DatatypeProperty))
        g.add((URIRef(schema + subject), URIRef(schema + "identifier"), Literal(row["isbn13"], datatype=XSD.int)))
        g.add((URIRef(schema + subject), URIRef(schema + "author"), URIRef(schema + row["authors"], datatype=XSD.string)))
        g.add((URIRef(schema + subject), URIRef(schema + "aggregateRating"), Literal(row["average_rating"], datatype=XSD.float)))
        g.add((URIRef(schema + subject), URIRef(schema + "inLanguage"), Literal(schema, lang=row["language_code"])))
        g.add((URIRef(schema + subject), URIRef(schema + "numberOfPages"), Literal(row["num_pages"], datatype=XSD.int)))
        g.add((URIRef(schema + subject), URIRef(schema + "datePublished"), Literal(row["publication_date"], datatype=XSD["date"])))
        g.add((URIRef(schema + subject), URIRef(schema + "publisher"), URIRef(schema + row["publisher"], datatype=XSD.string)))
        g.add((URIRef(schema + subject), URIRef(schema + "position"), URIRef(schema + row["book_number"], datatype=XSD.int)))

        # If the book isn't a standalone, but rather part of a series, I assign it as part of it through OWL
        if row["series"] != "Standalone":
            g.add((URIRef(schema + subject), OWL.oneOf, Literal(row["series"])))
            g.add((URIRef(schema + subject), URIRef(schema + "partOfSeries"), URIRef(schema + row["series"], datatype=XSD.string)))

    g.remove((None, None, URIRef("https://schema.org/unknown")))

    # print(g.serialize(format="turtle").decode("utf-8"))
    return g.serialize(destination='output.owl', format='turtle')
    # print(g.serialize(format="turtle").decode())


def random_book(data):
    num = random.randint(1, (len(data) + 1))
    return data.iloc[num]


def author_search(data, author):
    search = author.lower()
    search = search.replace(' ', '_')

    results = {}

    for ind in data.index:
        if search in data['authors'][ind]:
            val = data['bookID'][ind]
            results[val] = []
            results[val].append(data['bookID'][ind])
            results[val].append(data['title'][ind])
            results[val].append(data['authors'][ind])
            results[val].append(data['average_rating'][ind])
            results[val].append(data['language_code'][ind])
            results[val].append(data['num_pages'][ind])
            results[val].append(data['publication_date'][ind])
            results[val].append(data['publisher'][ind])
            results[val].append(data['series'][ind])
            results[val].append(data['book_number'][ind])

    return results


def book_search(data, author):
    search = author
    search = search.replace(' ', '_')

    results = {}

    for ind in data.index:
        if search in data['title'][ind]:
            val = data['bookID'][ind]
            results[val] = []
            results[val].append(data['bookID'][ind])
            results[val].append(data['title'][ind])
            results[val].append(data['authors'][ind])
            results[val].append(data['average_rating'][ind])
            results[val].append(data['language_code'][ind])
            results[val].append(data['num_pages'][ind])
            results[val].append(data['publication_date'][ind])
            results[val].append(data['publisher'][ind])
            results[val].append(data['series'][ind])
            results[val].append(data['book_number'][ind])

    return results


def sparql():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    # Spørring som henter alle bøkene som en forfatter (her: J.K. Rowling) har skrevet
    sparql.setQuery("""
    select ?book ?bookLabel where
    { ?book wdt:P50 wd:Q34660.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }

    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["book"]["value"], "   ", result["bookLabel"]["value"])

    # Spørring som henter sjangrene til en bok eller en serie av bøker (her: Harry Potter), siden datasettet vårt ikke inkluderer sjangre
    sparql.setQuery("""
    select ?genre ?genreLabel where
    { wd:Q43361 wdt:P136 ?genre.
       SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }

    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["genre"]["value"], "   ", result["genreLabel"]["value"])

    # Spørring som finner 10 bøker som har samme sjanger som en bok eller serie (her: Harry Potter)
    sparql.setQuery("""
    select ?book ?bookLabel where
    { wd:Q43361 wdt:P136 ?genre.
     ?book wdt:P136 ?genre.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
     }
     limit 10""")

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["book"]["value"], "   ", result["bookLabel"]["value"])

    # Spørring som henter alle bøker av en bestemt forfatter, som har samme sjanger som en bestemt forfatter (her: Harry Potter og J.K. Rowling)
    sparql.setQuery("""
    select distinct ?book ?bookLabel where
    { wd:Q43361 wdt:P136 ?genre.
     ?book wdt:P136 ?genre.
     ?book wdt:P50 wd:Q34660.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["book"]["value"], "   ", result["bookLabel"]["value"])


if __name__ == '__main__':
    #triples(csv_loader())
    sparql()
    MyApp().run()
