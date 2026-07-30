import os

from flask import Flask

from routes.tasks import tasks_bp

app = Flask(__name__, static_folder="public", static_url_path="")
app.register_blueprint(tasks_bp)


@app.get("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(port=port)
