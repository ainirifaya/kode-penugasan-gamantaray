import os
from flask import Flask, render_template_string, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data monitoring kapal
DATA = {
    "kecepatan": "1.5 m/s",
    "posisi": "X: 120, Y: 450",
    "navigasi": "LURUS",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Kapal Gamantaray</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #ffffff; text-align: center; padding: 20px; }
        .card { background: #1e1e1e; display: inline-block; padding: 20px; border-radius: 12px; margin: 10px; min-width: 180px; border: 1px solid #333; }
        h1 { color: #00d2d3; margin-bottom: 30px; }
        .val { font-size: 24px; font-weight: bold; color: #ff9f43; margin-top: 5px; }
        img { border-radius: 8px; border: 2px solid #00d2d3; margin-top: 15px; max-width: 500px; width: 100%; }
    </style>
</head>
<body>
    <h1>Dashboard Monitoring Kapal</h1>
    <div>
        <div class="card"><h3>Kecepatan</h3><p class="val">{{ data.kecepatan }}</p></div>
        <div class="card"><h3>Posisi Kapal</h3><p class="val">{{ data.posisi }}</p></div>
        <div class="card"><h3>Status Navigasi</h3><p class="val">{{ data.navigasi }}</p></div>
    </div>
    <h2>Foto Hasil Deteksi</h2>
    <img src="/hasil_foto.jpg" alt="Citra Objek">
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, data=DATA)

# Citra hasil deteksi diambil dari file lokal (hasil_foto.jpg di folder yang sama dengan file ini)
@app.route('/hasil_foto.jpg')
def foto():
    return send_from_directory(BASE_DIR, "hasil_foto.jpg")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
