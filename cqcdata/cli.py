import cqcdata.cqcdata as cqc
import click
import sqlite3

@click.command()
@click.option('--dbname', default='cqc_data.db',  help='SQLite database name')
@click.argument('command')
def cli(dbname,command):
    click.echo('Using SQLite3 database: {}'.format(dbname))
    if command == 'collect':
        con = cqc.setdb(dbname)
        cqc._getDatasetURLs() 
        cqc._get_care_directory(con)
        #cqc._get_active_locations(con)
        #cqc._get_ratings(con)
