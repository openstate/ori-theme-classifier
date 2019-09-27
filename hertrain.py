import os
import pickle
import random
import re
import shutil  # needed because symlinks don't work on windows
from datetime import datetime
from random import shuffle

import pandas as pd
import requests
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from stop_words import get_stop_words

from app.models import Feedback


def preprocess(text):
    # INPUT: een string vanuit de API, vaak met html-tags, stopwoorden etc.
    # OUTPUT: een string met onnozele en nietszeggende woorden verwijdert, bovendien terug gebracht naar de stam van het woord
    text = text.lower()
    text = re.sub("<\w*>", '', text)
    text = re.sub("<\w*\s\/>", '', text)
    text = re.sub("^https?:\/\/.*[\r\n]*", '', text)
    text = re.sub('\\\\x\S.', '', text)
    text = re.sub('[^a-z\s]', '', text)
    text = re.sub("\s+", " ", text)
    stopwords = get_stop_words("dutch") #Laa
    text = ' '.join([word for word in text.split() if word.lower() not in stopwords]) # Verwijder stopwoorden
    text = ' '.join([word for word in text.split() if len(word)>1]) # verwidjert woorden van 1 letter
    stemmer = SnowballStemmer("dutch")
    text = stemmer.stem(text)
    return text

modelBestanden = ["bestuurOndersteuning","veiligheid","verkeerVervoerWaterstaat","economie","onderwijs","sportCultuurRecreatie","sociaalDomein","volksgezondheidMilieu","volkshuisvestingRuimtelijkeOrdening"] 
print("start everything")
print("Query the IDs of Data")


df = pd.DataFrame()
listOfFeedbackModels = Feedback.query.all() # Vraag alle documenten op waarmee je kan hertrainen

print("In totaal zijn er zoveel documenten waarop getraind wordt: " + str(len(listOfFeedbackModels)))


print("Retrieve the data from the API")

oldID = "temp" # Variabele om mee te checken of je een nieuwe ORI-API call moet maken

i = 0 # Wordt gebruikt om te laten zien hoe het updaten gaat
k= 0 # Wordt gebruikt om te laten zien hoe het updaten gaat

for item in listOfFeedbackModels: # Loop over alle ids waarop getraind moet worden en vraag ze op aan de ORI API
	
	# Stukje die over hoeveel duizendste is opgehaald van de ORI API
	if i%(len(listOfFeedbackModels)/1000) < 1:
		print(str(k) + " /1000 van de documenten opgehaald")
		k+=1
	i+=1

	docID = item.id.split("-",1) #De ids bestaan ofwel uit alleen een ID of uit een ID en URL. Ze zijn verbonden met een streepje, dat wordt nu gesplitst. 
	check = 0 # variabele die is checkt of we het juiste document hebben, aangezien de IDs niet uniek zijn in ORI. 

	if docID[0] is not oldID: 
		jsonDoc = requests.get("http://api.openraadsinformatie.nl/v0/combined_index/events/"+docID[0]).json() #Vraag het document op bijpassend bij de id
		oldID = docID[0] # Zo kan je checken of het ID het zelfde blijft bij volgende documenten

	if len(docID) is 1: # Check of je een van de bijlages moet hebben of 
		if "description" in jsonDoc.keys(): # Dit is nodig omdat de IDs van ORI niet uniek zijn.
			tekst = preprocess(jsonDoc["name"] + " " + jsonDoc["description"]) # Vraag de relevante velden op en preprocess ze.
			check = 1
	else: # Bijlage nodig
		if "sources" in jsonDoc.keys(): # Wederom nodig vanwege niet unieke IDs
			for underlyingDoc in jsonDoc["sources"]: # Loop over alle bijlages
				if underlyingDoc["url"] == docID[1]: # Komen ze overeen, dan refereert dit document met de ID
					tekst = preprocess(underlyingDoc["description"])
					check = 1
					break


	if len(tekst.split()) > 100 and check == 1: # Dit een check op dat documenten wel lang genoeg moeten zijn en dat er daadwerkelijk een document is gevonden met het ID
		df = df.append(pd.DataFrame([[item.id, tekst, item.bestuurOndersteuning,item.veiligheid,item.verkeerVervoerWaterstaat,item.economie,item.onderwijs,item.sportCultuurRecreatie,item.sociaalDomein,item.volksgezondheidMilieu,item.volkshuisvestingRuimtelijkeOrdening]], 
			columns=["id","tekst","bestuurOndersteuning","veiligheid","verkeerVervoerWaterstaat","economie","onderwijs","sportCultuurRecreatie","sociaalDomein","volksgezondheidMilieu","volkshuisvestingRuimtelijkeOrdening"]))

print("Data is in, start TFIDF")

df = df.sample(frac=1).reset_index(drop=True)
tfidfModel = TfidfVectorizer(max_df=0.6,min_df=0.0005)
x = tfidfModel.fit_transform(df["tekst"])

newpath = "models/"+datetime.today().strftime('%Y-%m-%d')

if not os.path.exists(newpath):
    os.makedirs(newpath)

print("TFIDF done")

# Sla de nieuwe TFIDF op
pickle.dump(tfidfModel, open(newpath+ "/tfidf.pickle", "wb"))

for bestand in modelBestanden:

	# Creer een lijst met target values
	y = df[bestand]
	y= y.where(y < 1, 1)
	y= y.where(y >= 1, 0)

	# Zorg voor een eerlijke sampling, dus evenveel positieve als negative samples
	negatives = y.index[y==0].tolist()
	positives = y.index[y==1].tolist() 
	negatives = random.sample(negatives, len(positives))
	negatives.extend(positives)
	indexes = negatives
	shuffle(indexes)

	# Verdeel in een test- en trainset
	trainIndexes = indexes[:round(0.8*len(indexes))] 
	testIndexes = indexes[round(0.8*len(indexes)):] 
	print("training size of " + bestand + " is " + str(len(trainIndexes)) + ", testsize is " + str(len(testIndexes)))

	# Train het model
	model = LogisticRegression(C= 10, penalty= 'l2', solver= 'liblinear',dual=False,max_iter=250).fit(x[trainIndexes], y[trainIndexes])

	# F1-scores berekenen van de nieuwe modellen
	prediction = model.predict_proba(x[testIndexes])[:,0]
	for threshold in [0.2,0.3,0.4,0.5,0.6,0.7,0.8]:
		print("The threshold was " + str(threshold)+ " and the f1-score is " + str(round(f1_score(y[testIndexes], prediction<threshold),2)))

	# Sla de nieuwe modellen op
	pickle.dump(model, open(newpath +"/"+bestand+ ".pickle", "wb"))

latestpath = "models/latest"
# if os.path.exists(latestpath):
#     os.unlink(latestpath)
# os.symlink(newpath, latestpath)

# needed because symlinks don't work on windows
if not os.path.exists(latestpath):
    os.makedirs(latestpath)

# needed because symlinks don't work on windows
for root, dirs, files in os.walk(newpath):
	for file_ in files:
		src_file = os.path.join(newpath, file_)
		dst_file = os.path.join(latestpath, file_)
		if os.path.exists(dst_file):
			os.remove(dst_file)
		shutil.copy(src_file, latestpath)

r = requests.get('http://nginx/reload')

print(r.status_code, r.text)
