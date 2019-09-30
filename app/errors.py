from app import app, db
from flask import jsonify


@app.errorhandler(400)
def bad_request_error(error):
    response = jsonify(description=error.description, status_code=error.code, status=error.name)
    response.status_code = error.code
    return response


@app.errorhandler(404)
def not_found_error(error):
    response = jsonify(description=error.description, status_code=error.code, status=error.name)
    response.status_code = error.code
    return response


@app.errorhandler(500)
def handle_500(error):
    db.session.rollback()
    original = getattr(error, "original_exception", None)
    if original:
        message = '%s: %s' % (original.__class__.__name__, str(original))
    else:
        message = '%s: %s' % (error.__class__.__name__, str(error))
    response = jsonify(description=message, status_code=500, status="Internal Server Error")
    response.status_code = 500
    return response
