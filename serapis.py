import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import openai

# Your configurations here
openai.api_key = '#'
chromedriver_path = './chromedriver-mac-x64/chromedriver'
csv_file_path = 'vaurlsshort.csv'

# Setup directories
html_directory = 'batch_html'
markdown_directory = 'batch_markdown'
if not os.path.exists(html_directory):
    os.makedirs(html_directory)
if not os.path.exists(markdown_directory):
    os.makedirs(markdown_directory)

# Function to process each URL
def process_url(row, update_ui):
    ansi, url = row['ansi'], row['url']
    html_file_path = os.path.join(html_directory, f"{ansi}.html")
    markdown_file_path = os.path.join(markdown_directory, f"{ansi}.md")

    # Web Scraping
    try:
        driver = webdriver.Chrome(service=Service(chromedriver_path))
        driver.get(url)
        with open(html_file_path, 'w', encoding='utf-8') as file:
            file.write(driver.page_source)
        driver.quit()
        update_ui(ansi, 'HTML', 'Clear')
    except Exception as e:
        update_ui(ansi, 'HTML', 'Error')
        return

    # HTML to Markdown
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        cleaned_html = soup.get_text()
        markdown_content = md(cleaned_html)
        with open(markdown_file_path, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
        update_ui(ansi, 'Markdown', 'Clear')
    except Exception as e:
        update_ui(ansi, 'Markdown', 'Error')
        return

    # GPT-3.5 Processing
    try:
        specific_query = "this is the markdown from a local government website. you are helping a citizen find their elected officials. please help this citizen by combing through the data and output a the name, district, phone number, email, and term expiration date for each official. officials will be called one of these options: mayor, town council member, city council member, board of supervisor memeber. some pages might have messages indicating that you don't have permission to access the page for those just simply reply that this page needs to be re-indexed"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"{markdown_content}\n\n{specific_query}",
            max_tokens=50
        )
        update_ui(ansi, 'OpenAI', 'Clear' if response else 'Error')
    except Exception as e:
        update_ui(ansi, 'OpenAI', 'Token Limit Exceeded' if 'token limit' in str(e).lower() else 'Error')

# Function to update UI
def update_ui(ansi, step, status):
    current_text = table_area.get("1.0", tk.END)
    updated_text = f"{current_text}\n{ansi} | {step}: {status}"
    table_area.delete("1.0", tk.END)
    table_area.insert("1.0", updated_text)
    window.update_idletasks()

# Function to start the process
def start_process():
    start_button['state'] = 'disabled'
    df = pd.read_csv(csv_file_path)
    total_urls = len(df)
    for index, row in df.iterrows():
        process_url(row, update_ui)
        progress_bar['value'] = (index + 1) / total_urls * 100
    start_button['state'] = 'normal'

# Tkinter UI setup
window = tk.Tk()
window.title("Web Scraping and Processing App")

table_area = scrolledtext.ScrolledText(window, width=100, height=20)
table_area.pack(pady=10)

progress_bar = ttk.Progressbar(window, orient='horizontal', length=300, mode='determinate')
progress_bar.pack(pady=20)

start_button = tk.Button(window, text="Start Process", command=lambda: threading.Thread(target=start_process).start())
start_button.pack(pady=10)

window.mainloop()
