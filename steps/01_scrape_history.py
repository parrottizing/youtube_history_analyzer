
import time
import csv
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.date_utils import parse_relative_date, get_last_month_range
except ImportError:
    # Fallback if running from root
    from utils.date_utils import parse_relative_date, get_last_month_range

def setup_driver():
    options = Options()
    # Use a local profile to persist login cookies
    user_data_dir = os.path.join(os.getcwd(), "chrome_data")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Stealth arguments
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Additional stealth
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def scrape_history():
    print("Starting YouTube History Scraper (Step 1)...")
    start_date, end_date = get_last_month_range()
    print(f"Targeting range: {start_date} to {end_date}")

    driver = setup_driver()
    
    try:
        driver.get("https://www.youtube.com/feed/history")
        time.sleep(3)

        # Login Check
        if " accounts.google.com" in driver.current_url or "Sign in" in driver.page_source:
             print("Please log in to YouTube in the opened browser window.")
             print("Waiting for login...")
             for _ in range(120):
                 if "accounts.google.com" not in driver.current_url and "feed/history" in driver.current_url:
                     print("Login detected.")
                     break
                 time.sleep(2)
        
        # Click "Videos" filter to exclude Shorts
        try:
            print("Applying 'Videos' filter...")
            # Locate the chip for "Videos"
            # It's usually inside yt-chip-cloud-chip-renderer
            # We look for the text "Videos" (or localized equivalent if needed, but assuming English or structure)
            # Better to use a broad strategy or ask user? Content is likely English based on file content.
            
            wait = WebDriverWait(driver, 10)
            # Try to find a chip that contains text "Videos"
            videos_chip = wait.until(EC.element_to_be_clickable((By.XPATH, "//yt-chip-cloud-chip-renderer//yt-formatted-string[contains(text(), 'Videos')] | //yt-chip-cloud-chip-renderer//span[contains(text(), 'Videos')]")))
            videos_chip.click()
            print("Filter 'Videos' clicked.")
            time.sleep(3) # Wait for reload
        except Exception as e:
            print(f"Warning: Could not click 'Videos' filter. Might already be active or selector issue. Error: {e}")

        # ensure output dir
        os.makedirs("data", exist_ok=True)
        
        collected_videos = []
        visited_links = set()
        reached_end = False
        loop_count = 0
        max_loops = 100 # Safety limit
        
        while not reached_end:
            loop_count += 1
            if loop_count > max_loops:
                print("Max loops reached.")
                break
                
            sections = driver.find_elements(By.TAG_NAME, "ytd-item-section-renderer")
            if not sections:
                time.sleep(2)
                continue

            last_section_date_val = None

            for section in sections:
                try:
                    header_el = section.find_element(By.ID, "header").text
                    section_date = parse_relative_date(header_el)
                    
                    if not section_date:
                        continue
                        
                    last_section_date_val = section_date

                    if section_date > end_date:
                        continue
                    
                    if section_date < start_date:
                        reached_end = True
                        break 

                    # Extract videos
                    # Robust selector for videos (filtering shorts via URL check just in case the UI filter missed some)
                    video_elements = section.find_elements(By.CSS_SELECTOR, "a[href*='/watch?v=']")
                    
                    print(f"    Section '{header_el}': Found {len(video_elements)} potential videos.")

                    for title_el in video_elements:
                        try:
                            title = title_el.text.strip()
                            link = title_el.get_attribute("href")
                            
                            if not title or not link:
                                continue
                            
                            # Double check it is not a short (if UI filter failed)
                            if "/shorts/" in link:
                                continue
                            
                            if link in visited_links:
                                continue
                                
                            visited_links.add(link)
                            collected_videos.append({
                                "Date": section_date,
                                "Title": title,
                                "Link": link
                            })
                        except:
                            pass
                            
                except Exception as e:
                    print(f"Error parsing section: {e}")
                    continue
            
            if reached_end:
                print("Reached start date limit.")
                break
                
            # Scroll
            prev_height = driver.execute_script("return document.documentElement.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(3) # Increased wait
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            if new_height == prev_height:
                # Try one more small scroll or wait
                time.sleep(2)
                
            # Additional check if we are stuck or went too far
            if last_section_date_val and last_section_date_val < start_date:
                 print(f"Last section date {last_section_date_val} is older than start date {start_date}")
                 reached_end = True

        print(f"Scraping complete. Found {len(collected_videos)} videos.")
        
        output_file = os.path.join("data", "01_raw_history.csv")
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Title', 'Link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for video in collected_videos:
                writer.writerow(video)
                
        print(f"Saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_history()
