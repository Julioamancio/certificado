
from flask import Blueprint, render_template, request, redirect, url_for, session
import json
import os
from uuid import uuid4
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
ARQUIVO_QUESTOES = 'questoes.json'
ARQUIVO_CERTIFICADOS = 'certificados.json'
ARQUIVO_USUARIOS = 'usuarios.json'

ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123*'

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == ADMIN_USER and request.form['senha'] == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin/admin_login.html', erro=True)
    return render_template('admin/admin_login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin.login'))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return wrap

@admin_bp.route('/')
@admin_required
def dashboard():
    questoes = carregar_questoes()
    certificados = carregar_certificados()
    usuarios = carregar_usuarios()

    # Métricas de questões
    total_questoes = len(questoes)
    por_nivel = {}
    por_tipo = {}
    for q in questoes:
        nivel = (q.get('nivel') or '').upper()
        tipo = q.get('tipo') or ''
        if nivel:
            por_nivel[nivel] = por_nivel.get(nivel, 0) + 1
        if tipo:
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    # Métricas de certificados
    total_certificados = len(certificados)
    certificados_list = [{"codigo": cod, **dados} for cod, dados in certificados.items()]

    def parse_data(s):
        try:
            return datetime.strptime(s, '%d/%m/%Y')
        except Exception:
            return datetime.min

    certificados_recentes = sorted(certificados_list, key=lambda c: parse_data(c.get('data', '01/01/1970')), reverse=True)[:10]

    # Métricas de usuários
    total_usuarios = len(usuarios)
    agora = datetime.now()
    usuarios_validos = 0
    for u in usuarios:
        try:
            validade = datetime.strptime(u.get('validade', '1970-01-01 00:00'), '%Y-%m-%d %H:%M')
            if agora <= validade:
                usuarios_validos += 1
        except Exception:
            pass

    return render_template(
        'admin/dashboard.html',
        total_questoes=total_questoes,
        por_nivel=por_nivel,
        por_tipo=por_tipo,
        total_certificados=total_certificados,
        certificados_recentes=certificados_recentes,
        total_usuarios=total_usuarios,
        usuarios_validos=usuarios_validos,
    )

@admin_bp.route('/questoes')
@admin_required
def listar_questoes():
    questoes = carregar_questoes()
    grupos = {}
    for q in questoes:
        nivel = (q.get('nivel') or '').upper()
        # Normaliza o tipo para evitar chaves diferentes por maiúsculas/variações
        tipo = (q.get('tipo') or '').lower()
        if not nivel:
            continue
        if nivel not in grupos:
            grupos[nivel] = {}
        if tipo not in grupos[nivel]:
            grupos[nivel][tipo] = []
        grupos[nivel][tipo].append(q)

    return render_template('admin/questoes.html', questoes=questoes, grupos=grupos)

@admin_bp.route('/questoes/nova', methods=['GET', 'POST'])
@admin_required
def nova_questao():
    if request.method == 'POST':
        print("📥 RECEBENDO POST")
        try:
            questoes = carregar_questoes()
            nova = {
                "id": str(uuid4())[:8],
                "nivel": request.form['nivel'],
                "tipo": request.form['tipo'],
                "enunciado": request.form['enunciado'],
                "audio": request.form.get('audio', ''),
                "alternativas": {
                    "A": request.form['A'],
                    "B": request.form['B'],
                    "C": request.form['C'],
                    "D": request.form['D']
                },
                "resposta": request.form['resposta']
            }
            print("✅ Questão montada:", nova)
            questoes.append(nova)
            salvar_questoes(questoes)
            print("💾 Questão salva no JSON")
            return redirect(url_for('admin.listar_questoes'))
        except Exception as e:
            print("❌ ERRO AO SALVAR:", e)
            return "Erro ao salvar questão"
    return render_template('admin/nova_questao.html', questao=None)

@admin_bp.route('/questoes/editar/<id>', methods=['GET', 'POST'])
@admin_required
def editar_questao(id):
    questoes = carregar_questoes()
    questao = next((q for q in questoes if q['id'] == id), None)
    if not questao:
        return "Questão não encontrada", 404
    if request.method == 'POST':
        questao['nivel'] = request.form['nivel']
        questao['tipo'] = request.form['tipo']
        questao['enunciado'] = request.form['enunciado']
        questao['audio'] = request.form.get('audio', '')
        questao['alternativas'] = {
            "A": request.form['A'],
            "B": request.form['B'],
            "C": request.form['C'],
            "D": request.form['D']
        }
        questao['resposta'] = request.form['resposta']
        salvar_questoes(questoes)
        return redirect(url_for('admin.listar_questoes'))
    return render_template('admin/nova_questao.html', questao=questao)

@admin_bp.route('/questoes/deletar/<id>')
@admin_required
def deletar_questao(id):
    questoes = carregar_questoes()
    questoes = [q for q in questoes if q['id'] != id]
    salvar_questoes(questoes)
    return redirect(url_for('admin.listar_questoes'))

def carregar_questoes():
    if os.path.exists(ARQUIVO_QUESTOES):
        try:
            with open(ARQUIVO_QUESTOES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_questoes(questoes):
    try:
        with open(ARQUIVO_QUESTOES, 'w', encoding='utf-8') as f:
            json.dump(questoes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("❌ ERRO AO ESCREVER JSON:", e)

def carregar_certificados():
    if os.path.exists(ARQUIVO_CERTIFICADOS):
        try:
            with open(ARQUIVO_CERTIFICADOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []
