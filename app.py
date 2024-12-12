from flask import Flask, request, render_template, send_file
import os
import PyPDF2
import csv
from docx import Document
from fpdf import FPDF
import unicodedata
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB


@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado."
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return "Nenhum arquivo selecionado."
    
    file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    text = ""

    if file_ext == '.pdf':
        text = process_pdf(uploaded_file)
    elif file_ext == '.txt':
        text = process_txt(uploaded_file)
    elif file_ext == '.csv':
        text = process_csv(uploaded_file)
    elif file_ext == '.docx':
        text = process_docx(uploaded_file)
    else:
        return "Formato de arquivo não suportado."

    # Extrair links do texto processado
    links = textForLink(text)

    # Realizar scraping e buscar termo
    search_term = request.form.get('search_term')  # Define um termo padrão
    results = scrape(links, search_term)

    # Gerar PDF com resultados
    pdf_path = create_pdf('\n'.join(results))
    

    return render_template('result.html', texts=results, pdf_path=pdf_path, search_term=search_term)

def process_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def process_txt(file):
    return file.read().decode('utf-8')

def process_csv(file):
    text = ''
    csv_reader = csv.reader(file.read().decode('utf-8').splitlines())
    for row in csv_reader:
        text += ', '.join(row) + '\n'
    return text

def process_docx(file):
    document = Document(file)
    text = ''
    for paragraph in document.paragraphs:
        text += paragraph.text + '\n'
    return text

def textForLink(text):
    urls = []
    text = text.replace('\n', '').replace('\r', '').replace(" ", "")
    page_links = re.findall(r'https?://[^\s]+(?:\.[^\s]+)?', text)
    urls.extend(page_links)
    links = urls[0]
    links = links.split(",")
    return links

def scrape(links, search_term):
    results = []

    for link in links:
        try:
            headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}
            response = requests.get(link, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            context = soup.find_all(string=re.compile(search_term))
            
            if context:
                [str(results.append(f"A palavra '{search_term}' foi encontrada no link: {link}."))]
            #else:
                #results.append(f"A palavra '{search_term}' NÃO foi encontrada no link: {link}.")
        except Exception as e:
            results.append(f"Erro ao acessar {link}: {e}")

    #results = ",".join(results)    
    #results = results.replace("-","").replace("\r","").replace("\n","") 
    print(results)       
    return results

def create_pdf(results):
    pdf = FPDF()
    pdf.add_page()
    #pdf.add_font("Lucida Sans Unicode", style="", fname="C:\Windows\Fonts\l_10646.ttf", uni=True)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, results)

    pdf_path = "resultado_busca.pdf"
    pdf.output(pdf_path)
    return pdf_path

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)



