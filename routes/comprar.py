from flask import Blueprint, render_template

comprar_bp = Blueprint('comprar', __name__)

@comprar_bp.route('/comprar')
def comprar():
    return render_template('comprar.html')
