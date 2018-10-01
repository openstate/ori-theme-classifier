#/usr/bin/env python
# -*- coding: utf-8 -*-
import locale
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

mail = Mail(app)

locale.setlocale(locale.LC_NUMERIC, 'nl_NL.UTF-8')

from app import routes, models, errors

if not app.debug:
    # Send email on errors
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['FROM'],
            toaddrs=app.config['ADMINS'],
            subject='[ORI Theme Classifier] website error',
            credentials=auth,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # Log info messages and up to file
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler(
        'logs/otc.log',
        maxBytes=1000000,
        backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ORI Theme Classifier startup')
