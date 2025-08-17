from app import create_app

app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
# This script initializes and runs the Flask application.
# The app is created using the factory function `create_app` from the `app` module