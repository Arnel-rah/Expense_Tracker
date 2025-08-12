from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('transaction.accueil'))
    # ... code d'inscription
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('transaction.accueil'))
    # ... code de connexion
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
