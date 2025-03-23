import requests
from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urljoin
from flask import Flask, render_template_string

app = Flask(_name_)

visited = set()

# Koneksi database global
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="web_scraper"
    )

# Insert data ke database
def insert_to_db(url, title, paragraph, cursor, db):
    sql = "INSERT INTO web_data (url, title, paragraph) VALUES (%s, %s, %s)"
    cursor.execute(sql, (url, title, paragraph))
    db.commit()

# DFS Scraper
def dfs(url, cursor, db):
    if url in visited:
        return
    visited.add(url)
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title = soup.find('h1').text if soup.find('h1') else ''
    paragraph = soup.find('p').text if soup.find('p') else ''
    
    print(f"Scraping {url} - {title}")
    insert_to_db(url, title, paragraph, cursor, db)
    
    links = soup.find_all('a')
    for link in links:
        href = link.get('href')
        next_url = urljoin(url, href)
        dfs(next_url, cursor, db)

# Flask Route untuk tampilkan tabel
@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM web_data")
    data = cursor.fetchall()
    cursor.close()
    db.close()
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web Data Table</title>
        <style>
            table { width: 70%; border-collapse: collapse; margin: 50px auto; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            h2 { text-align: center; }
        </style>
    </head>
    <body>
        <h2>Data Scraped dari Website</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>URL</th>
                <th>Judul Artikel</th>
                <th>Paragraf</th>
            </tr>
            {% for row in data %}
            <tr>
                <td>{{ row.id }}</td>
                <td>{{ row.url }}</td>
                <td>{{ row.title }}</td>
                <td>{{ row.paragraph }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, data=data)

if _name_ == '_main_':
    # STEP 1: Scraping & DFS masuk ke DB
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("TRUNCATE TABLE web_data")  # reset table sebelum scraping
    db.commit()
    
    start_url = "http://localhost/DFS/index.html"
    dfs(start_url, cursor, db)
    
    cursor.close()
    db.close()
    print("Selesai scraping, data dimasukkan ke database.")

    # STEP 2: Menjalankan Flask web server
    app.run(debug=True)