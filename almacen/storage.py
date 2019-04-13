from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from almacen.auth import login_required
from almacen.db import get_db

bp = Blueprint('storage', __name__)

@bp.route('/')
def index():
    db = get_db()
    products = db.execute(
        'SELECT p.id, prd_name, prd_manufacturer, current_units, warning_units, last_modified, author_id, usr_name'
        ' FROM products p JOIN users u ON p.author_id = u.id'
        ' ORDER BY last_modified DESC'
    ).fetchall()
    return render_template('storage/index.html', products=products)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        manufacturer = request.form['manufacturer']
        current_units = request.form['current_units']
        warning_units = request.form['warning_units']
        error = None

        if not manufacturer:
            manufacturer = 'MISSING'
        
        if not name:
            error = 'A product name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO products (prd_name, prd_manufacturer, current_units, warning_units, author_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (name, manufacturer, current_units, warning_units, g.user['id'])
            )
            db.commit()
            return redirect(url_for('storage.index'))

    return render_template('storage/create.html')


def get_product(id, check_author=False):
    product = get_db().execute(
        'SELECT p.id, prd_name, prd_manufacturer, current_units, warning_units, author_id, last_modified, usr_name'
        ' FROM products p JOIN users u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if product is None:
        abort(404, "Product id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return product


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    product = get_product(id)

    if request.method == 'POST':
        amount = int(request.form['amount'])
        current_units = product['current_units']
        current_units += amount
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE products SET current_units = ?'
                ' WHERE id = ?',
                (current_units, id)
            )
            db.commit()
            return redirect(url_for('storage.index'))

    return render_template('storage/update.html', product=product)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_product(id)
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('storage.index'))

