
from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/gestion_budget'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle de données
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Numeric(12, 2), nullable=False)
    categorie = db.Column(db.String(50), nullable=False)
    type_transaction = db.Column(db.String(10), nullable=False)

# Page d'accueil avec graphiques
@app.route('/')
def accueil():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    # Calculs financiers
    total_revenus = db.session.query(db.func.sum(Transaction.montant)).filter_by(type_transaction='revenu').scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant)).filter_by(type_transaction='depense').scalar() or 0
    budget_initial = 350000  # Votre budget de départ
    solde = budget_initial + total_revenus - total_depenses
    
    # Graphique des dépenses par catégorie (en base64 pour HTML)
    depenses = Transaction.query.filter_by(type_transaction='depense').all()
    categories = {}
    for t in depenses:
        categories[t.categorie] = categories.get(t.categorie, 0) + float(t.montant)
    
    plt.figure()
    plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    
    return render_template(
        'accueil.html',
        transactions=transactions,
        solde=solde,
        total_revenus=total_revenus,
        total_depenses=total_depenses,
        budget_initial=budget_initial,
        graph_url=graph_url
    )

# Ajouter une transaction
@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_transaction():
    if request.method == 'POST':
        nouvelle_transaction = Transaction(
            date=request.form['date'],
            description=request.form['description'],
            montant=request.form['montant'],
            categorie=request.form['categorie'],
            type_transaction=request.form['type_transaction']
        )
        db.session.add(nouvelle_transaction)
        db.session.commit()
        return redirect(url_for('accueil'))
    return render_template('ajouter.html')

# Générer une facture PDF
@app.route('/facture')
def generer_facture():
    transactions = Transaction.query.all()
    total_revenus = db.session.query(db.func.sum(Transaction.montant)).filter_by(type_transaction='revenu').scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant)).filter_by(type_transaction='depense').scalar() or 0
    solde = 350000 + total_revenus - total_depenses

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Rapport Budget Mensuel", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Solde Final: {solde} AR", ln=1, align='L')
    
    pdf.cell(200, 10, txt="Détail des Transactions:", ln=1, align='L')
    for t in transactions:
        pdf.cell(200, 10, txt=f"{t.date} | {t.description} | {t.montant} AR | {t.categorie}", ln=1)
    
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='facture_budget.pdf')
    return response

if __name__ == '__main__':
    app.run(debug=True)