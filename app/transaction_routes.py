from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Transaction, db
from fpdf import FPDF
from datetime import datetime
from flask import jsonify

transaction_bp = Blueprint('transaction', __name__)


@transaction_bp.route('/')
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

    return render_template('accueil.html',
                           transactions=transactions,
                           solde=solde,
                           total_revenus=total_revenus,
                           total_depenses=total_depenses,
                           budget_initial=budget_initial,
                           labels=labels,
                           values=values)

@transaction_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_transaction():
    if request.method == 'POST':
        date_str = request.form.get('date')
        description = request.form.get('description')
        montant = request.form.get('montant')
        categorie = request.form.get('categorie')
        type_transaction = request.form.get('type_transaction')

        if not date_str or not description or not montant or not categorie or not type_transaction:
            flash("Merci de remplir tous les champs.", "danger")
            return redirect(url_for('transaction.ajouter_transaction'))

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            montant = float(montant)
        except ValueError:
            flash("Format de date ou montant invalide.", "danger")
            return redirect(url_for('transaction.ajouter_transaction'))

        nouvelle_transaction = Transaction(
            date=date,
            description=description,
            montant=montant,
            categorie=categorie,
            type_transaction=type_transaction,
            user_id=current_user.id
        )
        db.session.add(nouvelle_transaction)
        db.session.commit()

        flash("Transaction ajoutée avec succès !", "success")
        return redirect(url_for('transaction.accueil'))

    return render_template('ajouter.html')

@transaction_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        date_str = request.form.get('date')
        description = request.form.get('description')
        montant = request.form.get('montant')
        categorie = request.form.get('categorie')
        type_transaction = request.form.get('type_transaction')

        if not date_str or not description or not montant or not categorie or not type_transaction:
            flash("Merci de remplir tous les champs.", "danger")
            return redirect(url_for('transaction.modifier_transaction', id=id))

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            montant = float(montant)
        except ValueError:
            flash("Format de date ou montant invalide.", "danger")
            return redirect(url_for('transaction.modifier_transaction', id=id))

        transaction.date = date
        transaction.description = description
        transaction.montant = montant
        transaction.categorie = categorie
        transaction.type_transaction = type_transaction

        db.session.commit()

        flash("Transaction modifiée avec succès.", "success")
        return redirect(url_for('transaction.accueil'))

    return render_template('modifier.html', transaction=transaction)

@transaction_bp.route('/supprimer/<int:id>', methods=['POST'])
@login_required
def supprimer_transaction(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction supprimée avec succès.", "success")
    return redirect(url_for('transaction.accueil'))

@transaction_bp.route('/facture')
@login_required
def generer_facture():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Bonjour, voici votre facture", ln=True, align='C')

    pdf_output = pdf.output(dest='S').encode('latin1')
    response = Response(pdf_output, mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'attachment; filename=facture.pdf'

    return response

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print(f"Méthode reçue: {request.method}")
    if current_user.is_authenticated:
        print("Utilisateur déjà authentifié, redirection vers accueil")
        return redirect(url_for('transaction.accueil'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"Données reçues - username: {username}, email: {email}, password: {password}")
        if not username or not email or not password:
            flash('Veuillez remplir tous les champs.', 'danger')
            print("Champs manquants dans le formulaire d'inscription")
            return redirect(url_for('auth.register'))
        username = username.strip()
        email = email.strip()
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé', 'danger')
            print("Nom d'utilisateur déjà pris")
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà enregistré', 'danger')
            print("Email déjà enregistré")
            return redirect(url_for('auth.register'))
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        try:
            db.session.commit()
            print("Inscription réussie, utilisateur ajouté")
        except Exception as e:
            print(f"Erreur lors de l'inscription: {e}")
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription.', 'danger')
            return redirect(url_for('auth.register'))
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        print("Redirection vers /auth/login")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"Méthode reçue: {request.method}")
    if request.method == 'GET':
        print("Rendu de la page de connexion")
    if current_user.is_authenticated:
        print("Utilisateur déjà authentifié, redirection vers accueil")
        return redirect(url_for('transaction.accueil'), code=302)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Données reçues - username: {username}, password: {password}")
        if not username or not password:
            flash('Veuillez remplir tous les champs.', 'danger')
            print("Champs manquants dans le formulaire de connexion")
            return redirect(url_for('auth.login'), code=302)
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Nom d’utilisateur inexistant.', 'danger')
            print(f"Utilisateur non trouvé pour username: {username}")
            return redirect(url_for('auth.login'), code=302)
        if not check_password_hash(user.password_hash, password):
            flash('Mot de passe incorrect.', 'danger')
            print(f"Mot de passe incorrect pour username: {username}")
            return redirect(url_for('auth.login'), code=302)
        try:
            login_user(user)
            print(f"Connexion réussie pour {username}, session créée")
        except Exception as e:
            print(f"Erreur lors de login_user: {e}")
            flash('Erreur lors de la connexion.', 'danger')
            return redirect(url_for('auth.login'), code=302)
        flash('Connexion réussie !', 'success')
        next_page = request.args.get('next')
        print(f"Redirection vers: {next_page or url_for('transaction.accueil')}")
        return redirect(next_page or url_for('transaction.accueil'), code=302)
    return render_template('auth/login.html')

@auth_bp.route('/check-username')
def check_username():
    username = request.args.get('username')
    print(f"Requête AJAX check-username pour: {username}")
    try:
        user = User.query.filter_by(username=username).first()
        return jsonify({
            'available': not user,
            'message': 'Ce nom d\'utilisateur est déjà pris' if user else 'Nom d\'utilisateur disponible'
        })
    except Exception as e:
        print(f"Erreur dans check-username: {e}")
        return jsonify({'available': False, 'message': 'Erreur serveur'}), 500

@auth_bp.route('/check-email')
def check_email():
    email = request.args.get('email')
    print(f"Requête AJAX check-email pour: {email}")
    try:
        user = User.query.filter_by(email=email).first()
        return jsonify({
            'available': not user,
            'message': 'Cet email est déjà enregistré' if user else 'Email disponible'
        })
    except Exception as e:
        print(f"Erreur dans check-email: {e}")
        return jsonify({'available': False, 'message': 'Erreur serveur'}), 500
    
    
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('auth.login'))