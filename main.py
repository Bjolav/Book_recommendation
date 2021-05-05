from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import pandas as pd


def csv_loader():
    # CSV file gets read
    csv_data = pd.read_csv("books.csv", error_bad_lines=False, encoding="utf-8")

    # Deletion of all rows we deem unnecessary
    del csv_data['bookID']
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



def main():
    csv_loader()
    g = Graph()
    g.parse("https://www.wikidata.org/wiki/Q571", format="xml")
    schema = Namespace("https://schema.org/")
    g.bind("schema", schema)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)


    csv_data = pd.read_csv("books.csv", error_bad_lines=False, encoding="utf-8")

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

    g.remove((None, None, URIRef("hhtps://schema.org/unknown")))

    #print(g.serialize(format="turtle").decode("utf-8"))
    g.serialize(destination='output.owl', format='turtle')