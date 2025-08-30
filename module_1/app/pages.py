from flask import Blueprint, render_template

# Initializing the blueprint for the page routes
bp = Blueprint("pages", __name__)

# Route for the About tab
@bp.route("/")
def about():
    return render_template("pages/about.html")

# Route for the Contact tab
@bp.route("/contact")
def contact():
    return render_template("pages/contact.html")

# Route for the Projects tab
@bp.route("/projects")
def projects():
    return render_template("pages/projects.html")
