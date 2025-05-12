from flask import Blueprint, render_template, request
import json
import os
from datetime import datetime
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import uuid

prova_bp = Blueprint('prova', __name__)
ARQUIVO_QUESTOES = 'questoes.json'
ARQUIVO_CERTIFICADOS = 'certificados.json'
ARQUIVO_USUARIOS = 'usuarios_testes.json'

def carregar_questoes():
    if os.path.exists(ARQUIVO_QUESTOES):
        with open(ARQUIVO_QUESTOES, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def email_ja_usado(email):
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            usados = json.load(f)
        return email in usados and usados[email].get('usado', False)
    return False

def marcar_email_como_usado(email):
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            usados = json.load(f)
    else:
        usados = {}

    usados[email] = {"usado": True}

    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(usados, f, indent=4, ensure_ascii=False)

@prova_bp.route('/prova/<nivel>/inicio')
def iniciar_prova(nivel):
    questoes = carregar_questoes()
    questoes_nivel = [q for q in questoes if q['nivel'].lower() == nivel.lower()]
    return render_template('prova_inicio.html', nivel=nivel.upper(), questoes=questoes_nivel)

@prova_bp.route('/prova/<nivel>/finalizar', methods=['POST'])
def finalizar_prova(nivel):
    questoes = carregar_questoes()
    questoes_nivel = [q for q in questoes if q['nivel'].lower() == nivel.lower()]
    respostas = request.form
    nome = respostas.get('nome')
    email = respostas.get('email')

    if email_ja_usado(email):
        return render_template('erro_email_ja_usado.html')


    acertos = 0
    for i, q in enumerate(questoes_nivel):
        correta = q['resposta']
        enviada = respostas.get(f'q{i+1}')
        if enviada == correta:
            acertos += 1
    nota = round((acertos / len(questoes_nivel)) * 100)

    if nota >= 60:
        codigo = str(uuid.uuid4())[:8].upper()
        caminho_certificado = gerar_certificado_pdf(nome, nivel.upper(), nota, codigo)
        salvar_em_certificados_json(codigo, nome, nivel.upper(), datetime.now())
        enviar_email_com_certificado(email, nome, caminho_certificado)
        marcar_email_como_usado(email)
        return render_template('resultado.html', nome=nome, nota=nota, aprovado=True)
    else:
        marcar_email_como_usado(email)
        return render_template('resultado.html', nome=nome, nota=nota, aprovado=False)

def gerar_certificado_pdf(nome, nivel, nota, codigo):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    imagem_path = 'static/img/certificado_modelo.png'
    img_largura = 280
    img_altura = img_largura * 9 / 16
    x = (297 - img_largura) / 2
    y = (210 - img_altura) / 2
    pdf.image(imagem_path, x=x, y=y, w=img_largura, h=img_altura)

    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(0, y + 80)
    pdf.cell(297, 10, nome, 0, 1, 'C')

    pdf.set_font('Arial', '', 14)
    pdf.set_xy(0, y + 105)
    pdf.cell(297, 10, f'Level: {nivel.upper()} | Score: {nota}%', 0, 1, 'C')

    data = datetime.now().strftime('%d/%m/%Y')
    pdf.set_font('Arial', '', 11)
    pdf.set_xy(x + 67, y + 135)
    pdf.cell(297, 10, f'Date: {data} | Certificate ID: {codigo}', 0, 1, 'C')

    os.makedirs('static/certificados', exist_ok=True)
    nome_arquivo = f'static/certificados/Certificado_{nome.replace(" ", "_")}_{nivel}.pdf'
    pdf.output(nome_arquivo)

    return nome_arquivo

def salvar_em_certificados_json(codigo, nome, nivel, data):
    if os.path.exists(ARQUIVO_CERTIFICADOS):
        with open(ARQUIVO_CERTIFICADOS, 'r', encoding='utf-8') as f:
            certificados = json.load(f)
    else:
        certificados = {}

    certificados[codigo] = {
        "nome": nome,
        "nivel": nivel,
        "data": data.strftime('%d/%m/%Y')
    }

    with open(ARQUIVO_CERTIFICADOS, 'w', encoding='utf-8') as f:
        json.dump(certificados, f, indent=4, ensure_ascii=False)

def enviar_email_com_certificado(destinatario, nome, caminho_certificado):
    msg = EmailMessage()
    msg['Subject'] = 'Your English Test Certificate'
    msg['From'] = 'englishproficiencytestforever@gmail.com'
    msg['To'] = destinatario
    msg.set_content(f"""Hello {nome},

Congratulations on completing your English proficiency test!
Please find attached your certificate in PDF format.

Best regards,
English Proficiency Test Team
""")
    with open(caminho_certificado, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(caminho_certificado))

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('englishproficiencytestforever@gmail.com', 'mqkyvrtgglgqbsgs')
        smtp.send_message(msg)
