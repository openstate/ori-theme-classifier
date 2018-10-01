from app import app, db


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organisation = db.Column(db.String(16), index=True)
    year = db.Column(db.Integer, index=True)
    vendor_country = db.Column(db.String(64), index=True)
    vendor_name = db.Column(db.String(128), index=True)
    amount = db.Column(db.Numeric(13, 2))
    description = db.Column(db.Text)
    country_code = db.Column(db.String(3), index=True)


# Create the tables above if they don't exist
db.create_all()
