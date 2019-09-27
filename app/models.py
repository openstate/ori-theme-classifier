from app import db


class Feedback(db.Model):
    id = db.Column(db.String(500), primary_key=True, index=True)
    bestuurOndersteuning = db.Column(db.Integer)
    veiligheid = db.Column(db.Integer)
    verkeerVervoerWaterstaat = db.Column(db.Integer)
    economie = db.Column(db.Integer)
    onderwijs = db.Column(db.Integer)
    sportCultuurRecreatie = db.Column(db.Integer)
    sociaalDomein = db.Column(db.Integer)
    volksgezondheidMilieu = db.Column(db.Integer)
    volkshuisvestingRuimtelijkeOrdening = db.Column(db.Integer)


# Create the tables above if they don't exist
db.create_all()
