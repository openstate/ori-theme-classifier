import json
import os
import pickle
import re

from flask import request, jsonify
from nltk.stem.snowball import SnowballStemmer
from stop_words import get_stop_words

from app import app, db
from app.models import Feedback

modelBestanden = [
    "bestuurOndersteuning",
    "veiligheid",
    "verkeerVervoerWaterstaat",
    "economie",
    "onderwijs",
    "sportCultuurRecreatie",
    "sociaalDomein",
    "volksgezondheidMilieu",
    "volkshuisvestingRuimtelijkeOrdening"
]

# Inladen van modellen die nodig zijn
if os.path.exists("models/latest/tfidf.pickle"):
    tfidfModel = pickle.load(open("models/latest/tfidf.pickle", "rb"))

    # Er zijn 9 aparte modellen voor de veschillende thema's. Dit stuk laadt deze modellen in en zet ze in een lijst zodat je erover heen kan loopen.
    classificatieModellen = []
    for bestand in modelBestanden:
        classificatieModellen.append(pickle.load(open("models/latest/"+bestand+ ".pickle", "rb")))

classificatieLabels = {}
labels_path = "models/latest/labels.json"
if os.path.exists(labels_path):
    print("Found labels, loading them now")
    with open(labels_path, 'r') as in_file:
        classificatieLabels = json.load(in_file)


def preprocess(text):
    """
    INPUT: een string vanuit de API, vaak met html-tags, stopwoorden etc.
    OUTPUT: een string met onnozele en nietszeggende woorden verwijdert
    """
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
    stemmer = SnowballStemmer("dutch")
    text = stemmer.stem(text)
    return text


def getUnderlyingDocs(data):
    """
    INPUT: data, JSON-file vanuit ORI-API zonder aangegeven thema's met daarin mogelijk onderliggende documenten;
    OUTPUT: listOfDocs, per onderliggend document een dict met een ID en een string van de inhoud van het document;
    """
    docID = data["ori_identifier"]
    text = data["name"] # Begin van de stringtekst waar de analyse overheen gaat
    if "text" in data.keys():
        text += " " + data["text"]
    listOfDocs = [{"id":docID, "tekst":text}] # Dit is niet een onderliggend document, maar de titel en de omschrijving van het agendapunt

    if "sources" in data.keys(): # Check of er onderliggende documenten zijn
        for doc in data["sources"]: # Loop over de onderliggende documenten
            if "description" in doc.keys():
                listOfDocs.append({"id":docID+"-"+doc["url"], "tekst":doc["note"]+" "+doc["description"]})
    return listOfDocs


def addLabels(data):
    """
    INPUT: Lijst van dicts met IDs en teksten
    OUTPUT: Dict met als key de IDs van documenten en als value de voorspelwaarde van de modellen.
    """
    finalDict = {}
    for doc in data:
        newDict = {}
        length = len(doc["tekst"].split())
        for clf, naam in zip(classificatieModellen, modelBestanden):
            leesbaar = classificatieLabels[naam]
            if length > 75:
                newDict[leesbaar] = clf.predict_proba(doc["matrix"])[0,0]
            else:
                newDict[leesbaar] = 1
        finalDict[doc["id"]] = newDict
    return finalDict


@app.route("/classificeer", methods=['POST'])
def classificeer():
    """
    INPUT: Dict vanuit de API met een agendapunt, met daarin mogelijk meerdere onderliggende documenten
    OUTPUT: Een JSON, met daarin een dict van alle onderliggende documenten uit de de input-dict, en per document en dict met voorspellingen van een thema.
    """
    if not tfidfModel or not classificatieModellen:
        return ("Geen modellen geladen, roep reload aan?", 500)

    data = request.get_json(force=True) # Dict direct uit de API als INPUT
    data = getUnderlyingDocs(data) # Haalt uit deze dict onderliggende documenten, en zet elk document als dict in een lijst met daarin het ID en de tekst
    for i in range(len(data)):
        data[i]["tekst"] = preprocess(data[i]["tekst"])
        data[i]["matrix"] = tfidfModel.transform([data[i]["tekst"]])
    data = addLabels(data)
    return jsonify(data)


@app.route("/feedback", methods=['POST'])
def geefFeedback():
    """
    INPUT: Een dict met een ID van een document en per thema een -1 of 1
    OUTPUT: Een JSON, met daarin een dict van alle onderliggende documenten uit de de input-dict, en per document en dict met voorspellingen van een thema.
    """
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
    return "", 204


@app.route("/reload", methods=['GET'])
def reload():
    """
    INPUT: Niets
    OUTPUT: Een Overzicht van de F1-scores per thema van de nieuw gemaakte modellen
    """
    if not os.path.exists("models/latest/tfidf.pickle"):
        return jsonify("models do not yet exist, run een hertrain?",501)

    # Inladen van modellen die nodig zijn
    tfidfModelTemp = pickle.load(open("models/latest/tfidf.pickle", "rb"))

    # Er zijn 9 aparte modellen voor de veschillende thema's. Dit stuk laadt deze modellen in en zet ze in een lijst zodat je erover heen kan loopen.
    classificatieModellenTemp = []
    for bestand in modelBestanden:
        classificatieModellenTemp.append(pickle.load(open("models/latest/"+bestand+ ".pickle", "rb")))
    tfidfModel = tfidfModelTemp
    classificatieModellen = classificatieModellenTemp
    return jsonify("reloading gelukt!!!")


if __name__ == "__main__":
    app.run(threaded=True)
