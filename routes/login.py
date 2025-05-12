from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import json

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        try:
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
        except FileNotFoundError:
            flash("Nenhum acesso encontrado. Tente novamente mais tarde.", 'danger')
            return render_template('login.html')

        for u in usuarios:
            if u['usuario'] == usuario and u['senha'] == senha:
                validade = datetime.strptime(u['validade'], "%Y-%m-%d %H:%M")
                agora = datetime.now()
                if agora <= validade:
                    return redirect(url_for('prova.iniciar_prova', nivel=u['nivel']))

                else:
                    flash("Acesso expirado. Por favor, compre novamente.", 'warning')
                    return render_template('login.html')

        flash("Usuário ou senha inválidos.", 'danger')
    return render_template('login.html')
