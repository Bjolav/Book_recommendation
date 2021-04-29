import pandas as pd

#her leses csv-filen
data = pd.read_csv('C:/Users/larsa/OneDrive/Skole/UiB/INFO216/Semesteroppgave/books.csv')

#her slettes kolonnene vi ikke skal ha med
del data['isbn']
del data['isbn13']
del data['ratings_count']
del data['text_reviews_count']

#her endrer man alle mellomrom med understrek for å gjøre det lettere å gjøre om til tripler senere
data = data.replace(' ', '_', regex=True)

#her slettes alle radene som har tomme verdier
data = data.dropna()

#her fjerner man alle rader der sidetall = 0
data = data[data.num_pages != 0]

#legger til nye kolonner der man får informasjon om hvilken serie boken tilhører, og hvilken nummer i rekken den er
data[['title', 'series']] = data['title'].str.split('(', 1, expand=True)
data[['series', 'book_number']] = data['series'].str.split('#', 1, expand=True)

#rydder opp i radene, slik at enkelte tegn på slutten av verdiene fjernes
data['book_number'] = data['book_number'].str.strip(')')
data['title'] = data['title'].str.strip('_')
data['series'] = data['series'].str.strip('_')
data['series'] = data['series'].str.strip(')')
data['publisher;;;'] = data['publisher;;;'].str.strip(';')
data = data.rename({'publisher;;;': 'publisher'}, axis=1)


#til slutt lagres datasettet som en ny csv-fil
data.to_csv('C:/Users/larsa/OneDrive/Skole/UiB/INFO216/Semesteroppgave/books-ny.csv', index=False)
