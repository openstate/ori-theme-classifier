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
def feedback():
    data = request.get_json(force=True)
    # hier code van feedback, data is op dit moment een dict
    return ("", 204)


@app.route("/hertrain", methods=['GET'])
def hertrain():
    # Overschrijven van modellen hier ook, dus hertrainen en opnieuw inladen
    return ("", 204)


if __name__ == "__main__":
    app.run(threaded=True)
