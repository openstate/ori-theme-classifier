from app import app
import click


# OTC
@app.cli.group()
def OTC():
    """ORI Theme Classifier commands"""
    pass


@OTC.command()
@click.option('--csv-file', default='')
def do_something(csv_file):
    """
    Add records to the database. NOTE: records are added even if
    they already exist, so only use this when loading the records for
    the first time or when adding new records
    """
