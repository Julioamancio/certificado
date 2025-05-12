import stripe
import random
import string
import json
from flask import Blueprint, request, redirect, url_for
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import smtplib
import os

pagamento_bp = Blueprint('pagamento', __name__)

# 🔐 CHAVE SECRETA DO STRIPE (REAL)
stripe.api_key = 'sk_live_51RJlFXFm2kA3my7dcKq8zPbPsGD61qsiZb6pKNiAJKfKxk70ywSfxKT4wQZ5kafAKeQZYYD4xBCqzHzclvQUsUy9004hJ8KCJU'

# ✅ IDs DE PREÇOS REAIS DO STRIPE
PRECOS_STRIPE = {
    # 'Teste': 'price_1RN1kHFm2kA3my7dX4xf8fvi',  # Comentado se quiser usar depois
    'b2': 'price_1RN1kHFm2kA3my7dX4xf8fvi',
    'c1': 'price_1RN1InFm2kA3my7d6NboZjce'
}

# 🔁 CRIAÇÃO DE CHECKOUT COM STRIPE
@pagamento_bp.route('/create-checkout-session/<nivel>', methods=['POST'])
def create_checkout_session(nivel):
    email_cliente = request.form['email']

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer_email=email_cliente,
        line_items=[{
            'price': PRECOS_STRIPE[nivel],
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('pagamento.sucesso', nivel=nivel, email=email_cliente, _external=True),
        cancel_url=url_for('home.homepage', _external=True),
    )
    return redirect(session.url, code=303)

# ✅ SUCESSO: gerar credenciais, salvar e enviar
@pagamento_bp.route('/pagamento/sucesso/<nivel>')
def sucesso(nivel):
    email = request.args.get('email')

    usuario = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    senha = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    validade = datetime.now() + timedelta(hours=48)

    novo_usuario = {
        "usuario": usuario,
        "senha": senha,
        "nivel": nivel,
        "validade": validade.strftime("%Y-%m-%d %H:%M")
    }

    caminho = 'usuarios.json'
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    else:
        dados = []

    dados.append(novo_usuario)

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4)

    # ✅ CORPO DO E-MAIL
    corpo_email = f"""
✅ Your payment for the {nivel.upper()} test was successful.

🧑‍💻 Your login credentials:
Username: {usuario}
Password: {senha}
Valid until: {validade.strftime('%d/%m/%Y %H:%M')}

🔗 Access your test here: http://localhost:5000/login

Good luck and thank you for choosing us!
"""

    try:
        msg = MIMEText(corpo_email)
        msg['Subject'] = f"Access to your {nivel.upper()} English Test"
        msg['From'] = 'englishproficiencytestforever@gmail.com'
        msg['To'] = email

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('englishproficiencytestforever@gmail.com', 'mqkyvrtgglgqbsgs')
            smtp.send_message(msg)

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Payment Confirmed</title>
            <style>
                body {{
                    background: linear-gradient(to right, #e0f7fa, #e1bee7);
                    font-family: 'Segoe UI', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .box {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 0 15px rgba(0,0,0,0.1);
                }}
                h2 {{
                    color: #2e7d32;
                }}
                p {{
                    font-size: 18px;
                    color: #444;
                    margin: 20px 0;
                }}
                a {{
                    display: inline-block;
                    padding: 12px 25px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                    border-radius: 8px;
                    transition: background 0.3s;
                }}
                a:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>✅ Payment Confirmed</h2>
                <p>Access credentials were sent to: <strong>{email}</strong>.</p>
                <a href="/login">Go to Login</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        return "❌ Error sending email. Please contact support."
