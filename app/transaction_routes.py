import pdb
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, make_response
from flask_login import login_required, current_user
from .models import Transaction, db
from fpdf import FPDF

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/')
@login_required
def accueil():
    return render_template('accueil.html')

@transaction_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_transaction():
    return render_template('ajouter.html')

@transaction_bp.route('/supprimer/<int:id>', methods=['POST'])
@login_required
def supprimer_transaction(id):
    return redirect(url_for('transaction.accueil'))

@transaction_bp.route('/facture')
@login_required
def generer_facture():
    return make_response(pdb.output(dest='S'))
