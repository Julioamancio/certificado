from flask import Blueprint, render_template, request
import os
import json

verificar_bp = Blueprint('verificar', __name__, url_prefix='/verificar')
ARQUIVO_CERTIFICADOS = 'certificados.json'

@verificar_bp.route('/', methods=['GET', 'POST'])
def verificar():
    resultado = None
    if request.method == 'POST':
        codigo = request.form['codigo'].strip().upper()
        certificados = carregar_certificados()
        resultado = certificados.get(codigo)

        # Debug temporário
        print("Código recebido:", codigo)
        print("Resultado encontrado:", resultado)

    return render_template('verificar.html', resultado=resultado)

def carregar_certificados():
    if os.path.exists(ARQUIVO_CERTIFICADOS):
        with open(ARQUIVO_CERTIFICADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}
