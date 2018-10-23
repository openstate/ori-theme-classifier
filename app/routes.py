import csv
import os
import sys

# Inladen van libraries
import pickle
import pandas as pd
import json
import numpy as np
import re
import requests
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from stop_words import get_stop_words

from flask import (
    request, redirect, url_for, flash, Markup, jsonify
)

from app import app, db
from app.models import Feedback

from datetime import datetime


# Inladen van modellen die nodig zijn
tfidfModel = pickle.load(open("tfidf.pickle", "rb")) 

# Er zijn 9 aparte modellen voor de veschillende thema's. Dit stuk laadt deze modellen in en zet ze in een lijst zodat je erover heen kan loopen.
modelBestanden = ["bestuurOndersteuning","veiligheid","verkeerVervoerWaterstaat","economie","onderwijs","sportCultuurRecreatie","sociaalDomein","volksgezondheidMilieu","volkshuisvestingRuimtelijkeOrdening"] 
classificatieModellen = []
for bestand in modelBestanden:
    classificatieModellen.append(pickle.load(open("models/"+bestand+ ".pickle", "rb")))


def preprocess(text):
    # INPUT: een string vanuit de API, vaak met html-tags, stopwoorden etc.
    # OUTPUT: een string met onnozele en nietszeggende woorden verwijdert
    text = text.lower()
    text = re.sub("<\w*>", '', text)
    text = re.sub("<\w*\s\/>", '', text)
    text = re.sub("^https?:\/\/.*[\r\n]*", '', text)
    text = re.sub('\\\\x\S.', '', text)
    text = re.sub('[^a-z\s]', '', text)
    text = re.sub("\s+", " ", text)
    stopwords = get_stop_words("dutch") #Laa
    text = ' '.join([word for word in text.split() if word.lower() not in stopwords]) # Verwijder stopwoorden
    text = ' '.join([word for word in text.split() if len(word)>1]) #remove 1 letter words
    return text

def getUnderlyingDocs(data):
    ### INPUT: data, JSON-file vanuit ORI-API zonder aangegeven thema's met daarin mogelijk onderliggende documenten;
    ### OUTPUT: listOfDocs, per onderliggend document een dict met een ID en een string van de inhoud van het document;
    docID = data["id"]
    text = data["name"] # Begin van de stringtekst waar de analyse overheen gaat
    if "description" in data.keys():
        text += " " + data["description"]
    listOfDocs = [{"id":docID, "tekst":text}] # Dit is niet een onderliggend document, maar de titel en de omschrijving van het agendapunt 

    if "sources" in data.keys(): # Check of er onderliggende documenten zijn
        for doc in data["sources"]: # Loop over de onderliggende documenten
            if "description" in doc.keys():
                listOfDocs.append({"id":docID+"-"+doc["url"], "tekst":doc["note"]+" "+doc["description"]})
    return listOfDocs

def addLabels(data):
    ### INPUT: Lijst van dicts met IDs en teksten
    ### OUTPUT: Dict met als key de IDs van documenten en als value de voorspelwaarde van de modellen. 
    finalDict = {}
    for doc in data:
        newDict = {}
        for clf, naam in zip(classificatieModellen, modelBestanden):
           newDict[naam] = clf.predict_proba(doc["matrix"])[0,0]
        finalDict[doc["id"]] = newDict
    return finalDict

@app.route("/classificeer", methods=['POST'])
def classificeer():
    ### INPUT: Dict vanuit de API met een agendapunt, met daarin mogelijk meerdere onderliggende documenten
    ### OUTPUT: Een JSON, met daarin een dict van alle onderliggende documenten uit de de input-dict, en per document en dict met voorspellingen van een thema. 
    data = request.get_json(force=True) # Dict direct uit de API als INPUT
    data = getUnderlyingDocs(data) # Haalt uit deze dict onderliggende documenten, en zet elk document als dict in een lijst met daarin het ID en de tekst
    for i in range(len(data)):
        data[i]["tekst"] = preprocess(data[i]["tekst"])
        data[i]["matrix"] = tfidfModel.transform([data[i]["tekst"]])
    data = addLabels(data)
    return jsonify(data) 

@app.route("/feedback", methods=['POST'])
def geefFeedback():
    ### INPUT: Een dict met een ID van een document en per thema een -1 of 1
    ### OUTPUT: Een JSON, met daarin een dict van alle onderliggende documenten uit de de input-dict, en per document en dict met voorspellingen van een thema. 
    data = request.get_json(force=True)
    item = Feedback.query.get(data["id"]) 
    if item: # Controleer of het document al in de database staat, als dat zo is, update dan de informatie
        item.bestuurOndersteuning += data["bestuurOndersteuning"]
        item.veiligheid += data["veiligheid"]
        item.verkeerVervoerWaterstaat += data["verkeerVervoerWaterstaat"]
        item.economie += data["economie"]
        item.onderwijs += data["onderwijs"]
        item.sportCultuurRecreatie += data["sportCultuurRecreatie"]
        item.sociaalDomein += data["sociaalDomein"]
        item.volksgezondheidMilieu += data["volksgezondheidMilieu"]
        item.volkshuisvestingRuimtelijkeOrdening += data["volkshuisvestingRuimtelijkeOrdening"]
    else: # Voeg de informatie toe
        feedback = Feedback(
            id=data["id"],
            bestuurOndersteuning=data["bestuurOndersteuning"],
            veiligheid=data["veiligheid"],
            verkeerVervoerWaterstaat=data["verkeerVervoerWaterstaat"],
            economie=data["economie"],
            onderwijs=data["onderwijs"],
            sportCultuurRecreatie=data["sportCultuurRecreatie"],
            sociaalDomein=data["sociaalDomein"],
            volksgezondheidMilieu=data["volksgezondheidMilieu"],
            volkshuisvestingRuimtelijkeOrdening=data["volkshuisvestingRuimtelijkeOrdening"]
            )
        db.session.add(feedback)
    db.session.commit()
    return ("", 204)


@app.route("/hertrain", methods=['GET'])
def hertrain():
    ### INPUT: Niets
    ### OUTPUT: Een Overzicht van de F1-scores per thema van de nieuw gemaakte modellen 
    
    df = pd.DataFrame()
    listOfFeedbackModels = Feedback.query.all() # Vraag alle documenten op waarmee je kan hertrainen
    oldID = "temp" # Variabele om mee te checken of je een nieuwe ORI-API call moet maken

    for item in listOfFeedbackModels:
        docID = item.id.split("-",1)
        if docID[0] is not oldID:
            jsonDoc = requests.get("http://api.openraadsinformatie.nl/v0/combined_index/events/"+docID[0]).json()
            oldID = docID[0] # Zo kan je checken of het ID het zelfde blijft bij volgende documenten
        if len(docID) is 1: # Dit betekent dat het niet een bijlage is
            tekst = preprocess(jsonDoc["name"] + " " + jsonDoc["description"])
        else:
            if "sources" in jsonDoc.keys():
                for underlyingDoc in jsonDoc["sources"]:
                    if underlyingDoc["url"] == docID[1]: # Komen ze overeen, dan refereert dit document met de ID
                        tekst = preprocess(underlyingDoc["description"])
                        break

        if len(tekst.split()) > 100: # Dit een check op dat documenten wel lang genoeg moeten zijn
            df = df.append(pd.DataFrame([[item.id, tekst, item.bestuurOndersteuning,item.veiligheid,item.verkeerVervoerWaterstaat,item.economie,item.onderwijs,item.sportCultuurRecreatie,item.sociaalDomein,item.volksgezondheidMilieu,item.volkshuisvestingRuimtelijkeOrdening]], 
                columns=["id","tekst","bestuurOndersteuning","veiligheid","verkeerVervoerWaterstaat","economie","onderwijs","sportCultuurRecreatie","sociaalDomein","volksgezondheidMilieu","volkshuisvestingRuimtelijkeOrdening"]))
    
    df = df.sample(frac=1).reset_index(drop=True)
    tfidfModel = TfidfVectorizer(max_df=0.4,min_df=0.001)
    x = tfidfModel.fit_transform(df["tekst"])

    # Sla de nieuwe TFIDF op
    pickle.dump(tfidfModel, open("tfidf.pickle", "wb"))

    f1scores = []
    classificatieModellen = []
    for bestand in modelBestanden:
        y = df[bestand]
        y= y.where(y < 1, 1)
        y= y.where(y >= 1, 0)
        model = LogisticRegression(C= 10, penalty= 'l2', solver= 'liblinear',dual=False,max_iter=250).fit(x[:round(0.8*len(y))], y[:round(0.8*len(y))])
        classificatieModellen.append(model)
        
        # F1-scores berekenen van de nieuwe modellen
        prediction = model.predict_proba(x[round(0.8*len(y)):])[:,0]
        f1scores.append(round(f1_score(y[round(0.8*len(y)):], prediction<0.6),2))
        
        #Sla de nieuwe modellen op
        pickle.dump(model, open("models/"+bestand+ ".pickle", "wb"))
        
    return jsonify(str(f1scores))


if __name__ == "__main__":
    app.run(threaded=True)