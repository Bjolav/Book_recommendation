from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL
import pandas as pd


def csv_lifter():
    # her leses csv-filen
    csv_data = pd.read_csv("books.csv", error_bad_lines=False, encoding="utf-8")

    # her slettes kolonnene vi ikke skal ha med
    del csv_data['isbn']
    del csv_data['isbn13']
    del csv_data['ratings_count']
    del csv_data['text_reviews_count']

    # her endrer man alle mellomrom med understrek for å gjøre det lettere å gjøre om til tripler senere
    csv_data = csv_data.replace(' ', '_', regex=True)

    # her slettes alle radene som har tomme verdier
    csv_data = csv_data.dropna()

    # her fjerner man alle rader der sidetall = 0
    csv_data = csv_data[csv_data.num_pages != 0]

    # legger til nye kolonner der man får informasjon om hvilken serie boken tilhører, og hvilken nummer i rekken den er
    csv_data[['title', 'series']] = csv_data['title'].str.split('(', 1, expand=True)
    csv_data[['series', 'book_number']] = csv_data['series'].str.split('#', 1, expand=True)

    # rydder opp i radene, slik at enkelte tegn på slutten av verdiene fjernes
    csv_data['book_number'] = csv_data['book_number'].str.strip(')')
    csv_data['title'] = csv_data['title'].str.strip('_')
    csv_data['series'] = csv_data['series'].str.strip('_')
    csv_data['series'] = csv_data['series'].str.strip(')')
    csv_data['publisher;;;'] = csv_data['publisher;;;'].str.strip(';')
    csv_data = csv_data.rename({'publisher;;;': 'publisher'}, axis=1)


def main():
    g = Graph()
    g.parse("sparql.owl", format="xml")
    schema = Namespace("https://schema.org/")
    g.bind("schema", schema)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    g.bind("owl", OWL)


    csv_data = pd.read_csv("books.csv", error_bad_lines=False, encoding="utf-8")

    # csv_data = csv_data.fillna("unknown")

    for index, row in csv_data.iterrows():
        subject = row['title']

        g.add((URIRef(schema + subject), RDF.type, URIRef(schema + "identifier"), Literal(row["bookID"])))
        g.add((URIRef(schema + subject), URIRef(schema + "author"), URIRef(schema + row["authors"])))
        g.add((URIRef(schema + subject), RDF.type, OWL.onProperty, URIRef(schema + "aggregateRating"), Literal(row["average_rating"])))
        g.add((URIRef(schema + subject), URIRef(schema + "inLanguage"), URIRef(schema + row["language_code"])))
        g.add((URIRef(schema + subject), URIRef(schema + "numberOfPages"), Literal(row["num_pages"])))
        g.add((URIRef(schema + subject), URIRef(schema + "datePublished"), Literal(row["publication_date"])))
        g.add((URIRef(schema + subject), URIRef(schema + "publisher"), URIRef(schema + row["publisher"])))


    g.remove((None, None, URIRef("hhtps://schema.org/")))

    print(g.serialize(format="turtle").decode())