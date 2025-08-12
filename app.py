from flask import Flask, render_template, request, redirect, url_for, make_response, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from flask import abort, flash, redirect, url_for
import matplotlib.pyplot as plt
import io
import base64
import os
import requests
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELE DE DONNEE
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    avatar_url = db.Column(db.String(255))

    def set_avatar(self):
        self.avatar_url = f"https://ui-avatars.com/api/?name={self.username}&background=4F46E5&color=fff"

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, 
            method='pbkdf2:sha256',
            salt_length=16
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Numeric(12, 2), nullable=False)
    categorie = db.Column(db.String(50), nullable=False)
    type_transaction = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ROUTES D'AUTHENTIFICATION
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('accueil'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        errors = False
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé', 'danger')
            errors = True

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà enregistré', 'danger')
            errors = True

        if len(username) < 3:
            flash('Le nom d\'utilisateur doit contenir au moins 3 caractères', 'danger')
            errors = True

        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères', 'danger')
            errors = True

        if errors:
            return render_template('auth/register.html', 
                                username=username, 
                                email=email)

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            user.set_avatar()
            db.session.add(user)
            db.session.commit()
            
            flash('Inscription réussie! Vous pouvez maintenant vous connecter', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription', 'danger')
            app.logger.error(f"Erreur inscription: {str(e)}")

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('accueil'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Nom d\'utilisateur ou mot de passe invalide', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('accueil'))
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/check-username')
def check_username():
    username = request.args.get('username', '').strip()
    
    # Validation de base
    if len(username) < 3:
        return jsonify({
            'available': False,
            'message': 'Le nom doit contenir au moins 3 caractères'
        }), 400
    
    # Vérification des caractères autorisés
    if not username.isalnum() and '_' not in username:
        return jsonify({
            'available': False,
            'message': 'Utilisez seulement lettres, chiffres et underscores'
        }), 400

    # Vérification existence
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Nom déjà utilisé' if exists else 'Nom disponible'
    })
# ROUTES PRINCIPALES
@app.route('/')
@login_required
def accueil():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    total_revenus = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='revenu', user_id=current_user.id).scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='depense', user_id=current_user.id).scalar() or 0
    budget_initial = 350000
    solde = budget_initial + total_revenus - total_depenses

    depenses = Transaction.query.filter_by(type_transaction='depense', user_id=current_user.id).all()
    categories = {}
    for t in depenses:
        categories[t.categorie] = categories.get(t.categorie, 0) + float(t.montant)

    labels = list(categories.keys())
    values = list(categories.values())

    return render_template(
        'accueil.html',
        transactions=transactions,
        solde=solde,
        total_revenus=total_revenus,
        total_depenses=total_depenses,
        budget_initial=budget_initial,
        labels=labels,
        values=values
    )

@app.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_transaction():
    if request.method == 'POST':
        transaction = Transaction(
            date=request.form['date'],
            description=request.form['description'],
            montant=request.form['montant'],
            categorie=request.form['categorie'],
            type_transaction=request.form['type_transaction'],
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction ajoutée avec succès', 'success')
        return redirect(url_for('accueil'))
    return render_template('ajouter.html')

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_transaction(id):
    abort = ()
    transaction = Transaction.query.get_or_404(id)
    if transaction.author != current_user:
        abort(403)
    
    if request.method == 'POST':
        transaction.date = request.form['date']
        transaction.description = request.form['description']
        transaction.montant = request.form['montant']
        transaction.categorie = request.form['categorie']
        transaction.type_transaction = request.form['type_transaction']
        db.session.commit()
        flash('Transaction modifiée avec succès', 'success')
        return redirect(url_for('accueil'))
    return render_template('modifier.html', transaction=transaction)


# from flask import abort, flash, redirect, url_for

@app.route('/supprimer/<int:id>', methods=['POST'])
@login_required
def supprimer_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user != current_user:
        abort(403)
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction supprimée avec succès', 'success')
        return redirect(url_for('accueil'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
        return redirect(url_for('accueil'))

@app.route('/facture')
@login_required
def generer_facture():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    total_revenus = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='revenu', user_id=current_user.id).scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='depense', user_id=current_user.id).scalar() or 0
    solde = 350000 + total_revenus - total_depenses

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Quicksand", size=14)

    pdf.cell(200, 10, txt=f"Rapport Budget Mensuel - {current_user.username}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Solde Final: {solde} AR", ln=1, align='L')

    pdf.cell(200, 10, txt="Détail des Transactions:", ln=1, align='L')
    for t in transactions:
        pdf.cell(200, 10, txt=f"{t.date} | {t.description} | {t.montant} AR | {t.categorie}", ln=1)

    response = make_response(pdf.output(dest='S'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=f'facture_{current_user.username}.pdf')
    return response

# COMMANDES CLI
@app.cli.command('initdb')
def initdb_command():
    """Initialise la base de données."""
    db.create_all()
    print('Base de données initialisée.')

if __name__ == '__main__':
    app.run(
        debug=True,
        ssl_context=('server.crt', 'server.key'),
        host='0.0.0.0',
        port=443
    )