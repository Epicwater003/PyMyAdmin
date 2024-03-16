from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from app.auth import login_required
from app.db import get_inner_db
from app.setup import connection_required, get_connection
import pymysql
import werkzeug
bp = Blueprint('admin', __name__)


# # TODO: Write check for existing connection, that redirects user to connection setup page
@bp.before_app_request
def db_connection():
    pass


@bp.route('/', methods=('GET', 'POST'))
@login_required
@connection_required
def index():

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        ' SHOW TABLES;'
    )
    tables = cursor.fetchall()
    tbls = []
    for table in tables:
        tbl = {}
        for value in table.values():
            tbl['name'] = value
            cursor.execute(f"SELECT count(*) as c FROM {value};")
        tbl['count'] = cursor.fetchone()['c']
        tbls.append(tbl)

    cursor.execute(
        ' SHOW PROCEDURE STATUS WHERE Db = "flask";'
    )
    procedures = cursor.fetchall()
    cursor.execute(
        'SHOW FUNCTION STATUS WHERE Db = "flask";'
    )
    functions = cursor.fetchall()
    cursor.execute('SELECT * FROM information_schema.parameters WHERE SPECIFIC_NAME = "place_order";')
    #print(cursor.fetchall())
    out = []
    if request.method == "POST":
        try:
            name = request.form.get('pf_name')
            params = request.form.get('input')
            try:
                params = list(map(int,params.split(',')))
                params = str(params)[1:-1]
            except:
                params = ""
            cursor.execute(f'CALL {name}({params});')
            get_connection().commit()
            out = cursor.fetchall()
        except pymysql.err.OperationalError as e:
            flash(f'Неверно введены параметры!{e}')

    return render_template('admin/index.html', tables=tbls, procedures = procedures, functions = functions, out=out)


@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        try:
            query = ""
            c = 0
            for i, field in enumerate(request.form.items()):
                if not i:
                    query += f" CREATE TABLE {field[1]} ( \n" \
                             f" id_{field[1]} INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n"
                else:
                    if (i-1)%3 == 0:
                        query += field[1] + " "
                    elif (i-1)%3 == 1:
                        query += field[1] + " "
                    else:
                        query += field[1] + ", "
            query = query[:-2]
            query += ');'
            print(query)
            cursor = get_connection().cursor()
            cursor.execute(query)
        except pymysql.err.OperationalError as e:
            flash(f"Ошибка ввода!, {e}")

    return render_template('admin/create.html')


@bp.route('/<name>/view/', methods=('GET', 'POST'))
def view(name):
    cursor = get_connection().cursor()
    cursor.execute(f' SELECT * FROM {name};')
    table = cursor.fetchall()
    keys = table[0].keys()
    cursor.execute(f' DESCRIBE {name};')
    description = cursor.fetchall()
    return render_template('admin/view.html', table_name=name, table=table, keys=keys, description=description)


@bp.route('/<name>/alter')
def alter(name):
    return render_template('admin/alter.html', table_name=name)


@bp.route('/<name>/update', methods=('GET', 'POST'))
def update(name):

    if request.method == 'POST':
        cursor = get_connection().cursor()
        cursor.execute(f' SELECT * FROM {name};')
        table = cursor.fetchall()
        if table:
            keys = [i for i in table[0].keys()]
        else: keys = []
        cursor.execute(f' DESCRIBE {name};')
        description = cursor.fetchall()
        try:
            d = []
            k = []
            for i, key in enumerate(keys):
                if not description[i]['Extra'] == 'auto_increment':
                    k.append(key)
                    if 'int' in description[i]['Type']:
                        d.append(int(request.form[f'{key}']))
                    else:
                        d.append(request.form[f'{key}'])
            d = str(d)[1:-1]
            k = str(k)[1:-1].replace("'", "")
            cursor.execute(f' INSERT INTO {name} ({k})'
                           f' VALUES({d});')
            get_connection().commit()
        except werkzeug.exceptions.BadRequestKeyError:
            try:
                row = request.form['remove_button']
                cursor.execute(f' DELETE FROM {name} WHERE {keys[0]} = {row}')
                get_connection().commit()
            except ValueError as e:
                flash(f'Ошибка типа данных! {e}')
            except pymysql.err.IntegrityError as e:
                flash(f'Ошибка внесения данных! {e}')
            except pymysql.err.OperationalError as e:
                flash(f'Ошибка ввода данных! {e}')
            except pymysql.err.DataError as e:
                flash(f'Слишком большое значение! {e}')

        except ValueError as e:
            flash(f'Ошибка типа данных! {e}')
        except pymysql.err.IntegrityError as e:
            flash(f'Ошибка внесения данных! {e}')
        except pymysql.err.OperationalError as e:
            flash(f'Ошибка ввода данных! {e}')
        except pymysql.err.DataError as e:
            flash(f'Слишком большое значение! {e}')

    cursor = get_connection().cursor()
    cursor.execute(f' SELECT * FROM {name};')
    table = cursor.fetchall()
    if table:
        keys = [i for i in table[0].keys()]
    else:
        keys = []
    cursor.execute(f' DESCRIBE {name};')
    description = cursor.fetchall()

    return render_template('admin/update.html', table_name=name, table=table, keys=keys, description=description)


@bp.route('/<name>/delete', methods=('GET', 'POST'))
def delete(name):
    if request.method == 'POST':
        try:
            cursor = get_connection().cursor()
            cursor.execute(f' DROP TABLE {name};')
            get_connection().commit()
            return redirect(url_for('index'))
        except pymysql.err.OperationalError as e:
            flash(f'Невозможно удалить таблицу из за внешних связей! {e}')

    return render_template('admin/delete.html', table_name=name)
