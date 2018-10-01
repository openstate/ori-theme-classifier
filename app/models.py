from app import app, db


class Feedback(db.Model):
    id = db.Column(db.String(500), primary_key=True, index=True)
    bestuurEnBeleid = db.Column(db.Integer)
    veiligheid = db.Column(db.Integer)
    onderwijs = db.Column(db.Integer)
    economie = db.Column(db.Integer)
    verkeer = db.Column(db.Integer)
    sociaal = db.Column(db.Integer)
    volkshuisvesting = db.Column(db.Integer)
    gezondheid = db.Column(db.Integer)
    cultuur = db.Column(db.Integer)


# Create the tables above if they don't exist
db.create_all()
