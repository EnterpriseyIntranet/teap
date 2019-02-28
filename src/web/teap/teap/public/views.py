"""Public section, including homepage and signup."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required

from teap.public.forms import LoginForm
from teap.utils import flash_errors

blueprint = Blueprint('public', __name__, template_folder='./templates')


@blueprint.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        return redirect(url_for('core.index'))
        # if form.validate_on_submit():
        #     login_user(form.user)
        #     flash('You are logged in.', 'success')
        #     redirect_url = request.args.get('next') or url_for('core.index')
        #     return redirect(redirect_url)
        # else:
        #     flash_errors(form)
    return render_template('login.html', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    """Logout."""
    logout_user()
    flash('You are logged out.', 'info')
    return redirect(url_for('public.login'))
