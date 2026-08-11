import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_all_questions(start_url):
    all_data = []
    current_url = start_url
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        while current_url:
            print(f"Scraping: {current_url}")
            page.goto(current_url)
            page.wait_for_selector(".question")
            
            # Extract data (logic from previous step)
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            # ... (Insert your data extraction logic here) ...
            question_data = {
                "question_text": soup.select_one(".question").text.strip(),
                # Add other fields...
            }
            all_data.append(question_data)
            
            # Find the 'Next' button
            next_button = soup.find('a', string="NEXT")
            if next_button and next_button.has_attr('href'):
                current_url = "https://questions.examside.com" + next_button['href']
                time.sleep(1) # Be polite to the server
            else:
                current_url = None # Stop when no more 'Next' button
        
        browser.close()
        
    # Save all gathered data to a JSON file
    with open('jee_physics_questions.json', 'w') as f:
        json.dump(all_data, f, indent=4)

# scrape_all_questions('YOUR_START_URL_HERE')