import os
import uuid
from flask import Flask, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from models import db, Todo
from forms import TodoForm


# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secure Config from Environment
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
app.config["RECAPTCHA_PUBLIC_KEY"] = os.getenv("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = os.getenv("RECAPTCHA_PRIVATE_KEY")
app.config["TESTING"] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# HOME (CREATE + LIST)
@app.route("/", methods=["GET", "POST"])
def index():

    form = TodoForm()

    if form.validate_on_submit():

        image_filename = None

        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)

            unique_name = str(uuid.uuid4()) + "_" + filename
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            image_filename = unique_name

        new_task = Todo(task=form.task.data, image=image_filename)

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("index"))

    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    return render_template("index.html", form=form, todos=todos)


# DELETE
@app.route("/delete/<int:id>")
def delete(id):

    todo = Todo.query.get_or_404(id)

    if todo.image:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], todo.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(todo)
    db.session.commit()

    return redirect(url_for("index"))


# EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    todo = Todo.query.get_or_404(id)
    form = TodoForm(obj=todo)

    if form.validate_on_submit():

        todo.task = form.task.data

        if form.image.data:

            if todo.image:
                old_path = os.path.join(app.config["UPLOAD_FOLDER"], todo.image)
                if os.path.exists(old_path):
                    os.remove(old_path)

            file = form.image.data
            filename = secure_filename(file.filename)
            unique_name = str(uuid.uuid4()) + "_" + filename

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            todo.image = unique_name

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("edit.html", form=form, todo=todo)


if __name__ == "__main__":
    app.run(debug=True)
