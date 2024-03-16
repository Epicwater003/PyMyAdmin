from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from .auth import login_required
import functools
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import login_required
from app.db import get_inner_db

import pymysql

bp = Blueprint('setup', __name__, url_prefix='/setup')


@bp.before_app_request
def load_db_info():
    db_id = session.get('db_id')
    if db_id is None:
        g.db_connection_info = None
        g.db_connection = None
    else:
        g.db_connection_info = get_inner_db().execute(
            'SELECT * FROM database WHERE id = ?', (db_id,)
        ).fetchone()
        g.db_connection = pymysql.connect(
            host=g.db_connection_info['host'],
            port=int(g.db_connection_info['port']),
            user=g.db_connection_info['username'],
            password=g.db_connection_info['password'],
            database=g.db_connection_info['dbname'],
            cursorclass=pymysql.cursors.DictCursor
        )


def get_connection() -> pymysql.connections.Connection:
    return g.db_connection


@bp.route('/use', methods=['POST', 'GET'])
@login_required
def use():
    if request.method == 'POST':
        error = None

        try:
            db_id = request.form["submit_button"]
            db = get_inner_db()
            dbs = db.execute(
                ' SELECT *'
                ' FROM database as db'
                ' WHERE db.id == ?',
                db_id
            ).fetchone()
            if not dbs:
                error = f"Для записи №{db_id} нет доступных баз данных!"
            else:
                try:
                    # if g.db_connection is not None:
                    #     pass
                    g.db_connection = pymysql.connect(
                        host=dbs['host'],
                        port=int(dbs['port']),
                        user=dbs['username'],
                        password=dbs['password'],
                        database=dbs['dbname'],
                        cursorclass=pymysql.cursors.DictCursor
                    )
                    g.db_connection_info = dbs
                except Exception as e:
                    error = f"Невозможно подключиться к базе данных {dbs['dbname']}!"
                    print(e)
            if not error:
                session['db_id'] = db_id
                return redirect(url_for("index"))
            else:
                flash(error)
        except:
            db_id = request.form["remove_button"]
            db = get_inner_db()
            dbs = db.execute(
                ' SELECT *'
                ' FROM database as db'
                ' WHERE db.id == ?',
                db_id
            )
            if not dbs:
                error = f"Для записи №{db_id} нет доступных баз данных!"
            else:
                db.execute(
                    ' DELETE'
                    ' FROM database as db'
                    ' WHERE db.id == ?',
                    db_id
                ).fetchone()
                db.commit()

    db = get_inner_db()
    dbs = db.execute(
        ' SELECT db.id, db.dbname, db.username, db.host, db.port'
        ' FROM database as db'
    ).fetchall()

    if not dbs:
        return redirect(url_for("setup.new"))

    return render_template('setup/use.html', dbs=dbs)


@bp.route('/new', methods=['POST', 'GET'])
@login_required
def new():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        dbname = request.form['dbname']
        host = request.form['host']
        port = request.form['port']
        db = get_inner_db()
        error = None

        if not username:
            error = 'Необходимо ввести имя пользователя!'
        elif not password:
            error = 'Необходимо ввести пароль!'
        elif not dbname:
            error = 'Необходимо ввести название базы данных!'
        elif not host:
            error = 'Необходимо ввести адресс хоста!'
        elif not port:
            error = 'Необходимо ввести порт!'

        if error is None:
            try:
                connection = pymysql.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password,
                    database=dbname,
                    cursorclass=pymysql.cursors.DictCursor
                )
                db.execute(
                    "INSERT INTO database(username, password, dbname, host, port) VALUES (?, ?, ?, ?, ?)",
                    (username, password, dbname, host, port),
                )
                db.commit()
            except db.Error:
                error = "Ошибка внутренней базы данных!"
            except Exception as e:
                error = f"Отсутствует подключение к базе данных {dbname}. Запись не добавлена!"
                print(e)
            else:
                return redirect(url_for("setup.use"))

        flash(error)

    return render_template('setup/new.html')


@bp.route('/close')
def close():
    session['db_id'] = None
    return redirect(url_for('index'))


def connection_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.db_connection_info is None:
            return redirect(url_for('setup.use'))

        return view(**kwargs)

    return wrapped_view
