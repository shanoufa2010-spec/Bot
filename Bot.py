import discord
from discord.ext import commands
import os, json
from flask import Flask, render_template_string
from threading import Thread

app = Flask(__name__)
# المسار الذي ستضع فيه المجلدات التي تحتوي الصور
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_accounts():
    accounts = {}
    # مسح مجلدات الصور تلقائياً
    if os.path.exists(UPLOAD_FOLDER):
        for folder in sorted(os.listdir(UPLOAD_FOLDER)):
            folder_path = os.path.join(UPLOAD_FOLDER, folder)
            if os.path.isdir(folder_path):
                # نبحث عن أي صورة داخل المجلد
                images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                img_url = f"/{UPLOAD_FOLDER}/{folder}/{images[0]}" if images else ""
                accounts[folder] = {
                    "title": f"حساب ألعاب احترافي #{folder}",
                    "price": "10 USDT",
                    "img_url": img_url
                }
    return accounts

@app.route('/')
def index():
    return render_template_string("""
    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));">
        {% for id, acc in accounts.items() %}
        <div style="border:1px solid #5865F2; margin:10px; padding:10px;">
            <img src="{{ acc.img_url }}" style="width:100%">
            <h3>{{ acc.title }}</h3>
            <p>{{ acc.price }}</p>
        </div>
        {% endfor %}
    </div>
    """, accounts=get_accounts())

# ... بقية كود البوت (كما في الرد السابق) ...