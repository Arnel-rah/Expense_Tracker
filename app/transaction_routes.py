from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Transaction, db
from fpdf import FPDF
from datetime import datetime

transaction_bp = Blueprint('transaction', __name__)


@transaction_bp.route('/')
@login_required
def accueil():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()

    total_revenus = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='revenu', user_id=current_user.id).scalar() or 0

    total_depenses = db.session.query(db.func.sum(Transaction.montant))\
        .filter_by(type_transaction='depense', user_id=current_user.id).scalar() or 0

    budget_initial = 350000  # Ajuste selon ton besoin
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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('transaction.accueil'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        flash('donnée reçu: ' + username + password)
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Nom d’utilisateur ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash('Connexion réussie !', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('transaction.accueil'))

    return render_template('auth/accueil.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('transaction.accueil'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà enregistré', 'danger')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()

        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('auth.login'))