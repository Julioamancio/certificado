from flask import Flask
from routes.home import home_bp
from routes.comprar import comprar_bp
from routes.pagamento import pagamento_bp
from routes.login import login_bp
from routes.prova import prova_bp
from routes.admin import admin_bp
from routes.verificar_certificado import verificar_bp  # 🔁 Adicionado

app = Flask(__name__)
app.secret_key = 'chave-super-secreta'

# Blueprints registrados
app.register_blueprint(home_bp)
app.register_blueprint(comprar_bp)
app.register_blueprint(pagamento_bp)
app.register_blueprint(login_bp)
app.register_blueprint(prova_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(verificar_bp)  # 🔁 Registro do blueprint de verificação

if __name__ == '__main__':
    app.run(debug=True)
