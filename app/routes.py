import csv
import os
import sys

from flask import (
    request, redirect, url_for, flash, Markup, jsonify
)

from app import app, db
from app.models import Feedback

from datetime import datetime


@app.route("/", methods=['GET', 'POST'])
def index():
    return jsonify(1)


if __name__ == "__main__":
    app.run(threaded=True)
