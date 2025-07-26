from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy  # För databashantering
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # För säkra lösenord
import datetime
import uuid

# Skapa Flask-appen
app = Flask(__name__)
app.secret_key = 'din_hemliga_nyckel'  # Byt ut i produktion!

# Konfigurera databasen (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initiera databasen
db = SQLAlchemy(app)

# Initiera Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modell för användare
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    # Relation till todos (en användare har många todos)
    todos = db.relationship('Todo', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modell för todos
class Todo(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    klar = db.Column(db.Boolean, default=False)
    skapad = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    prioritet = db.Column(db.String(10), default='medel')
    
    # Främmande nyckel till användaren
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Skapa tabellerna (körs bara en gång)
with app.app_context():
    db.create_all()

# Funktion för att ladda användare (krävs av Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Kontextprocessor för att göra current_user tillgänglig i mallar
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.route('/profil')
@login_required
def profil():
    antal_todos = Todo.query.filter_by(user_id=current_user.id).count()
    return render_template('profil.html', 
                         användare=current_user,
                         antal_todos=antal_todos)



# Route för registrering
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Kontrollera om användarnamn redan finns
        if User.query.filter_by(username=username).first():
            flash('Användarnamnet finns redan')

        elif len(password) < 8:
            flash('Lösenordet måste vara minst 8 tecken')

        elif not any(char.isdigit() for char in password):
            flash('Lösenordet måste innehålla minst en siffra')

        else:
            # Skapa ny användare
            new_user = User(username=username)
            new_user.set_password(password)  # Hasha lösenordet
            
            # Spara till databasen
            db.session.add(new_user)
            db.session.commit()
            
            flash('Konto skapat! Vänligen logga in.')
            return redirect(url_for('login'))
    
    return render_template('register.html')

# Route för inloggning
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hämta användare från databasen
        user = User.query.filter_by(username=username).first()
        
        # Kontrollera användare och lösenord
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Fel användarnamn eller lösenord')
    
    return render_template('login.html')

# Route för startsidan
@app.route('/')
@login_required
def index():
    sortering = request.args.get('sortering', 'nyast')
    
    # Hämta aktuell användares todos
    todos = Todo.query.filter_by(user_id=current_user.id)
    
    # Sortering
    if sortering == 'nyast':
        todos = todos.order_by(Todo.skapad.desc())
    elif sortering == 'äldst':
        todos = todos.order_by(Todo.skapad.asc())
    elif sortering == 'prioritet':
        # Anpassad sortering för prioritet
        from sqlalchemy import case
        priority_order = case(
            {'hög': 1, 'medel': 2, 'låg': 3},
            value=Todo.prioritet
        )
        todos = todos.order_by(priority_order)
    
    return render_template('index.html', todos=todos.all(), sortering=sortering)

# Route för att lägga till todo
@app.route('/lägg_till', methods=['POST'])
@login_required
def lägg_till():
    text = request.form.get('text')
    prioritet = request.form.get('prioritet', 'medel')
    
    if text:
        # Skapa ny todo
        new_todo = Todo(
            id=str(uuid.uuid4()),
            text=text,
            prioritet=prioritet,
            user_id=current_user.id
        )
        
        # Spara till databasen
        db.session.add(new_todo)
        db.session.commit()
    
    return redirect(url_for('index'))

# Route för att markera todo som klar
@app.route('/klar/<id>')
@login_required
def markera_klar(id):
    todo = Todo.query.get(id)
    
    # Kontrollera att todo finns och tillhör inloggad användare
    if todo and todo.user_id == current_user.id:
        todo.klar = True
        db.session.commit()
    
    return redirect(url_for('index'))

# Route för att ta bort todo
@app.route('/ta_bort/<id>')
@login_required
def ta_bort(id):
    todo = Todo.query.get(id)
    
    # Kontrollera att todo finns och tillhör inloggad användare
    if todo and todo.user_id == current_user.id:
        db.session.delete(todo)
        db.session.commit()
    
    return redirect(url_for('index'))

# Route för att redigera todo
@app.route('/redigera/<id>', methods=['GET', 'POST'])
@login_required
def redigera_sida(id):
    todo = Todo.query.get(id)
    
    # Kontrollera att todo finns och tillhör inloggad användare
    if not todo or todo.user_id != current_user.id:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        ny_text = request.form.get('text')
        if ny_text:
            todo.text = ny_text
            db.session.commit()
            return redirect(url_for('index'))
    
    return render_template('redigera.html', todo=todo)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    felmeddelande = None
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Lösenordet är nu ändrat!', 'success')
            return redirect(url_for('login'))
        else:
            felmeddelande = 'Användaren finns inte.'
    return render_template('reset_password.html', felmeddelande=felmeddelande)

if __name__ == '__main__':
    app.run(debug=True)