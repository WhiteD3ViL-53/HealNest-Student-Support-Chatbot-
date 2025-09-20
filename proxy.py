from flask import Flask, redirect

app = Flask(__name__)

@app.route("/")
def home():
    return redirect("http://localhost:8501")

@app.route("/admin")
def admin():
    return redirect("http://localhost:8502")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
