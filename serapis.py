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
import csv
import requests

from openai import OpenAI

client = OpenAI(api_key='#')

# Your configurations here
chromedriver_path = './chromedriver-mac-x64/chromedriver'
csv_file_path = 'vaurlsshort.csv'
specific_query = "this is the markdown from a local government website. you are helping a citizen find their elected officials. please help this citizen by combing through the data and output a the name, district, phone number, email, and term expiration date for each official. officials will be called one of these options: mayor, town council member, city council member, board of supervisor memeber. some pages might have messages indicating that you don't have permission to access the page for those just simply reply that this page needs to be re-indexed"

# Setup directories
html_directory = 'batch_html'
markdown_directory = 'batch_markdown'
if not os.path.exists(html_directory):
    os.makedirs(html_directory)
if not os.path.exists(markdown_directory):
    os.makedirs(markdown_directory)

    # Process with GPT-4
def process_with_gpt4(ansi, markdown_content, specific_query, update_ui):
     # Ensure the 'response' directory exists
    response_directory = 'response'
    if not os.path.exists(response_directory):
        os.makedirs(response_directory)

    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You are a municipal clerk data scraping gpt."},
            {"role": "user", "content": f"{markdown_content}\n\n{specific_query}"}  # Use passed parameters
        ])
        update_ui(ansi, 'OpenAI', 'Clear')
        
            # Extract the response text
        response_text = response.choices[0].message.content.strip()

        # Define the path for the response file
        response_file_path = os.path.join(response_directory, f"{ansi}.txt")

        # Write the response to a file
        with open(response_file_path, 'w', encoding='utf-8') as file:
            file.write(response_text)
        
        print(f"OpenAI response saved for {ansi}")  # Optional: Confirmation message
        
        # Additional code to handle the response
    except openai.InvalidRequestError as e:
        print(f"Invalid request to OpenAI API: {e}")
        update_ui(ansi, 'OpenAI', 'Invalid Request')
    except openai.RateLimitError as e:
        print(f"Rate limit exceeded for OpenAI API: {e}")
        update_ui(ansi, 'OpenAI', 'Rate Limit Exceeded')
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        update_ui(ansi, 'OpenAI', 'API Error')
    except Exception as e:
        print(f"Unexpected error during OpenAI processing: {e}")
        if 'token limit' in str(e).lower():
            update_ui(ansi, 'OpenAI', 'Token Limit Exceeded')
        else:
            update_ui(ansi, 'OpenAI', 'Unexpected Error')

def update_sitemaps():
    update_ui('System', 'Update Sitemaps', 'In Progress')
    df = pd.read_csv('sitemaps.csv')  # Assuming 'sitemaps.csv' contains 'ansi' and 'url' columns
    sitemaps_directory = 'sitemaps'
    if not os.path.exists(sitemaps_directory):
        os.makedirs(sitemaps_directory)

    for _, row in df.iterrows():
        ansi, sitemap_url = row['ansi'], row['url']
        response_file_path = os.path.join(sitemaps_directory, f"{ansi}-sitemap.xml")

        try:
            response = requests.get(sitemap_url)
            if response.status_code == 200:
                with open(response_file_path, 'w', encoding='utf-8') as file:
                    file.write(response.text)
                update_ui(ansi, 'Sitemap', 'Saved')
            else:
                with open(response_file_path, 'w', encoding='utf-8') as file:
                    file.write("404")
                update_ui(ansi, 'Sitemap', '404')
        except Exception as e:
            update_ui(ansi, 'Sitemap', 'Error')
            print(f"Error fetching sitemap for {ansi}: {e}")

    update_ui('System', 'Update Sitemaps', 'Completed')

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
    
    # Process with GPT-4
    process_with_gpt4(ansi, markdown_content, specific_query, update_ui)



# Example usage within your processing loop
# Assuming 'ansi' is the identifier, 'markdown_content' is the content to process,
# and 'specific_query' is your query to GPT


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

def process_with_gpt4(ansi, markdown_content, specific_query, update_ui):
     # Ensure the 'response' directory exists
    response_directory = 'response'
    if not os.path.exists(response_directory):
        os.makedirs(response_directory)

    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You are a municipal clerk data scraping gpt."},
            {"role": "user", "content": f"{markdown_content}\n\n{specific_query}"}  # Use passed parameters
        ])
        update_ui(ansi, 'OpenAI', 'Clear')
        
            # Extract the response text
        response_text = response.choices[0].message.content.strip()

        # Define the path for the response file
        response_file_path = os.path.join(response_directory, f"{ansi}.txt")

        # Write the response to a file
        with open(response_file_path, 'w', encoding='utf-8') as file:
            file.write(response_text)
        
        print(f"OpenAI response saved for {ansi}")  # Optional: Confirmation message
        
        # Additional code to handle the response
    except openai.InvalidRequestError as e:
        print(f"Invalid request to OpenAI API: {e}")
        update_ui(ansi, 'OpenAI', 'Invalid Request')
    except openai.RateLimitError as e:
        print(f"Rate limit exceeded for OpenAI API: {e}")
        update_ui(ansi, 'OpenAI', 'Rate Limit Exceeded')
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        update_ui(ansi, 'OpenAI', 'API Error')
    except Exception as e:
        print(f"Unexpected error during OpenAI processing: {e}")
        if 'token limit' in str(e).lower():
            update_ui(ansi, 'OpenAI', 'Token Limit Exceeded')
        else:
            update_ui(ansi, 'OpenAI', 'Unexpected Error')

def create_table():
    # Iterate over each text file in the 'response' folder
    for filename in os.listdir('response'):
        if filename.endswith('.txt'):
            ansi = filename.split('.')[0]  # Extract ANSI code from filename
            with open(os.path.join('response', filename), 'r', encoding='utf-8') as file:
                text_content = file.read()

            # Scrub the data by removing or replacing commas
            scrubbed_text_content = text_content.replace(',', '')  # This removes all commas


            # Prepare the prompt for GPT-3.5-turbo
            prompt = f"Extract the name, district/role, email, and phone number from the following text for each individual. place it into a csv that has the format colums name,district,role,email,phone. Only output the data for the cells of the csv. do not output the headers. do not output any other message including normal greetings / pleasentries. \n{text_content}"

            try:
                response = client.chat.completions.create(model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ])

                # Process the response to extract structured data
                structured_data = response.choices[0].message.content.strip()

                 # Split the structured data into lines and prepend the ANSI code to each line
                structured_lines = structured_data.split('\n')
                structured_lines_with_ansi = [f"{ansi} , {line}" for line in structured_lines if line.strip() != '']


                # Save the structured data as a CSV file
                csv_file_path = os.path.join('response', f"{ansi}.csv")
                with open(csv_file_path, 'w', encoding='utf-8') as csv_file:
                    csv_file.write("ansi,name,district,role,email,phone\n")  # Write CSV header
                    for line in structured_lines_with_ansi:
                        csv_file.write(f"{line}\n")

                print(f"CSV file saved for {ansi}")

            except openai.OpenAIError as e:
                print(f"OpenAI API error for {ansi}: {e}")
            except Exception as e:
                print(f"Unexpected error for {ansi}: {e}")

def merge_csvs():
    output_file = 'merged_data.csv'
    csv_files = [file for file in os.listdir('response') if file.endswith('.csv')]
    
    with open(output_file, 'w', encoding='utf-8', newline='') as merged_file:
        writer = None
        for i, file in enumerate(csv_files):
            with open(os.path.join('response', file), 'r', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                if i == 0:
                    # Write the header for the first file
                    headers = next(reader)
                    writer = csv.writer(merged_file)
                    writer.writerow(headers)
                else:
                    # Skip the header for subsequent files
                    next(reader)
                
                # Write the data rows
                for row in reader:
                    writer.writerow(row)
    print("CSV files merged successfully.")


# Tkinter UI setup
window = tk.Tk()
window.title("Web Scraping and Processing App")

# Add a new button for updating sitemaps
update_sitemaps_button = tk.Button(window, text="Update Sitemaps", command=lambda: threading.Thread(target=update_sitemaps).start())
update_sitemaps_button.pack(pady=10)

table_area = scrolledtext.ScrolledText(window, width=100, height=20)
table_area.pack(pady=10)

progress_bar = ttk.Progressbar(window, orient='horizontal', length=300, mode='determinate')
progress_bar.pack(pady=20)

start_button = tk.Button(window, text="Start Process", command=lambda: threading.Thread(target=start_process).start())
start_button.pack(pady=10)

create_table_button = tk.Button(window, text="Create Table", command=create_table)
create_table_button.pack(pady=10)

merge_button = tk.Button(window, text="Merge CSVs", command=merge_csvs)
merge_button.pack(pady=10)

window.mainloop()

