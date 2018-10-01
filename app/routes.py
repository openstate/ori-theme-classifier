import csv
import os
import sys

from flask import (
    request, redirect, url_for, flash, Markup, jsonify
)

from app import app, db
from app.models import Feedback

from datetime import datetime


# Hier inladen modellen
#model1 = model 


@app.route("/classificeer", methods=['POST'])
def classificeer():
    data = request.get_json(force=True)
    # hier code van classifieer, data is op dit moment een dict

    return jsonify(data)


@app.route("/feedback", methods=['POST'])
def geefFeedback():
    data = request.get_json(force=True)
    item = Feedback.query.get(data["id"])
    if item:
        print("check")
        item.bestuurEnBeleid += data["bestuurEnBeleid"]
        # etc.
    else:
        feedback = Feedback(
            id=data["id"],
            #etc.
            )
        db.session.add(feedback)
    db.session.commit()
    return ("", 204)


@app.route("/hertrain", methods=['GET'])
def hertrain():
    # Overschrijven van modellen hier ook, dus hertrainen en opnieuw inladen
    listOfFeedbackModels = Feedback.query.all()
    return ("", 204)


if __name__ == "__main__":
    app.run(threaded=True)
