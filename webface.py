from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Markup,
    escape,
    flash,
)
import datetime
import functools
from sqlitewrap import SQLite
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError

app = Flask(__name__)
app.secret_key = b"totoj e zceLa n@@@hodny retezec nejlep os.urandom(24)"
app.secret_key = b"x6\x87j@\xd3\x88\x0e8\xe8pM\x13\r\xafa\x8b\xdbp\x8a\x1f\xd41\xb8"


def prihlasit(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if "user" in session:
            return function(*args, **kwargs)
        else:
            return redirect(url_for("login", url=request.path))

    return wrapper



@app.route("/", methods=["GET"])
def root():
    a = 3
    b = 8
    # a = 1 + '1'
    return render_template("base.html")


@app.route("/google/")
def google():
    return render_template("google.html")

@app.route("/vzkazy/", methods=["GET"])
def vzkazy():
    if 'user' not in session:
        flash("Tato stánka je pouze pro příhlášené!")
        return redirect(url_for("login", url=request.path))

    with SQLite("data.sqlite") as cursor:
        response = cursor.execute(
            "SELECT login, body, datetime FROM user JOIN message ON user.id = message.user_id ORDER BY datetime DESC"                    
        )
        response = response.fetchall()

    return render_template("vzkazy.html", response=response)

@app.route("/vzkazy/", methods=["POST"])
def vzkazy_post():
    if 'user' not in session:
       flash("Tato stánka je pouze pro příhlášené!")
       return redirect(url_for("login", url=request.path))     
     
    with SQLite("data.sqlite") as cursor:
        response = cursor.execute("SELECT id FROM user WHERE login=?", [session["user"]])
        response = response.fetchone()
        user_id = list(response)[0]

    vzkaz = request.form.get('vzkaz')
    if vzkaz:
        with SQLite("data.sqlite") as cursor:
            cursor.execute(
                "INSERT INTO message (user_id, body, datetime) VALUES (?, ?, ?)", 
                [user_id, vzkaz, datetime.datetime.now()],
            )

        print(vzkaz)
    return redirect(url_for("vzkazy"))

@app.route("/kalkulacka/", methods=["GET"])
def kalkulacka():
    if 'user' not in session:
        flash("Tato stánka je pouze pro příhlášené!")
        return redirect(url_for("login", url=request.path))
    
    a = request.args.get("a", 0)
    b = request.args.get("b", 0)
    try:
        c = int(a) + int(b)
    except ValueError:
        c = "Error"
    return render_template("kalkulacka.html", a=a, b=b, c=c)


@app.route("/registration/", methods=["GET"])
def registration():
    return render_template("registration.html")

@app.route("/registration/", methods=["POST"])
def registration_post():
    jmeno = request.form.get("jmeno", "")
    heslo1 = request.form.get("heslo1", "")
    heslo2 = request.form.get("heslo2", "")
    if len(jmeno) <5:
        flash("jméno je příliš krátké, musí mít alespon 5 znaků!")
        return redirect(url_for("registration"))
    if len(heslo1) <5: 
        flash("Heslo musí mít alespoň 5 znaků", "error")
        return redirect(url_for("registration"))
    if heslo1 != heslo2:
        flash("Musíte zadat dvakrát stejné heslo!", "error")
        return redirect(url_for("registration"))
    
    hash_ = generate_password_hash(heslo1)
    try:
        with SQLite('data.sqlite') as cursor:
            cursor.execute("INSERT INTO user (login, passwd) VALUES (?,?)", [jmeno, hash_])
            flash(f"Uživatel {jmeno} byl přidán!", "success")
    except IntegrityError:
        flash(f"Uživatel {jmeno} je již registrován", "error")
    return redirect(url_for("registration"))


@app.route("/login/", methods=["GET"])
def login():
    if "user" not in session:
        return render_template("login.html")
    return render_template("logout.html")

@app.route("/login/", methods=["POST"])
def login_post():
    jmeno = request.form.get("jmeno", "")
    heslo = request.form.get("heslo", "")
    url = request.args.get("url", "")
    with SQLite('data.sqlite') as cursor:
        response = cursor.execute(
            f"SELECT login, passwd FROM user WHERE login = ? ", [jmeno],
        )
        response = response.fetchone()
        if response:
            login, passwd = list(response)
            if check_password_hash(passwd, heslo):
                session["user"] = jmeno
                flash("Jsi přihlášen!", "success")
                if url:
                    return redirect(url)
                else:
                    return redirect(url_for("root"))
        flash("Nesprávné přihlašovací údaje!", "error")
        return redirect(url_for("login", url=url))


@app.route("/logout/")
def logout():
    session.pop("user", None)
    flash("Byl jsi odhlášen!", "success")
    return redirect(url_for("root"))
