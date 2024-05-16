from flask import Flask

from QuizManagerPackage import (
    errors,
    pages
)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'k0H$-2$Rb2*v'

    app.register_blueprint(pages.bp)
    app.register_error_handler(404, errors.page_not_found)
    return app