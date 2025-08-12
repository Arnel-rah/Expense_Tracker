from fpdf import FPDF
from flask import make_response
from flask_login import current_user
from .models import Transaction, db

def generer_facture_pdf():
    """Génère un PDF avec le rapport budgétaire de l'utilisateur connecté."""
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    total_revenus = db.session.query(db.func.sum(Transaction.montant)) \
        .filter_by(type_transaction='revenu', user_id=current_user.id).scalar() or 0
    total_depenses = db.session.query(db.func.sum(Transaction.montant)) \
        .filter_by(type_transaction='depense', user_id=current_user.id).scalar() or 0

    solde = 350000 + total_revenus - total_depenses

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)

    pdf.cell(200, 10, txt=f"Rapport Budget Mensuel - {current_user.username}", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Solde Final: {solde} AR", ln=1, align='L')

    pdf.cell(200, 10, txt="Détail des Transactions:", ln=1, align='L')
    for t in transactions:
        pdf.cell(200, 10, txt=f"{t.date} | {t.description} | {t.montant} AR | {t.categorie}", ln=1)

    response = make_response(pdf.output(dest='S'))
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=f'facture_{current_user.username}.pdf')
    return response
