```python
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))

        # Log in the user
        session['user_id'] = user.id
        flash('Login successful!')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        del session['user_id']
        flash('Logout successful.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
```

Note: This code assumes you have a `User` model defined in `app/models.py` with fields for `username` and `password`. The `db.session` is assumed to be initialized elsewhere in your application.