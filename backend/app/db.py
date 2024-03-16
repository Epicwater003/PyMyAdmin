import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash
from sql_datatypes import AccessLevel


def get_inner_db():
    if 'inner_db' not in g:
        g.inner_db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.inner_db.row_factory = sqlite3.Row

    return g.inner_db


def close_db(e=None):
    db = g.pop('inner_db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_inner_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
        db.execute(
            "INSERT INTO user(username, password, access_level)  VALUES (?, ?, ?);",
            ('admin', generate_password_hash('admin'), AccessLevel.Admin),
        )
        db.commit()


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
