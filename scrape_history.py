import time
import csv
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from date_utils import parse_relative_date, get_last_month_range

# import undetected_chromedriver as uc # Removed due to instability

def setup_driver():
    options = Options()
    # Use a local profile to persist login cookies
    user_data_dir = os.path.join(os.getcwd(), "chrome_data")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Stealth arguments to bypass "Browser not secure"
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    options.add_argument("--start-maximized")

    # Important: Re-initialize the standard chromedriver service
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Additional stealth: override navigator.webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def scrape_history():
    print("Starting YouTube History Scraper...")
    start_date, end_date = get_last_month_range()
    print(f"Targeting range: {start_date} to {end_date}")

    driver = setup_driver()
    
    try:
        driver.get("https://www.youtube.com/feed/history")
        time.sleep(3) # Wait for load

        # Check if logged in
        if " accounts.google.com" in driver.current_url or "Sign in" in driver.page_source:
             print("Please log in to YouTube in the opened browser window.")
             print("Waiting for login...")
             
             for i in range(120):
                 if "accounts.google.com" not in driver.current_url and "feed/history" in driver.current_url:
                     print("History page detected! Assuming logged in...")
                     break
                 
                 # Alternative check: Avatar button
                 if driver.find_elements(By.ID, "avatar-btn"):
                     print("Avatar detected! Navigating to History...")
                     driver.get("https://www.youtube.com/feed/history")
                     break
                     
                 time.sleep(2)
             else:
                 print("Login check timed out. Proceeding anyway...")

        
        collected_videos = []
        last_date_processed = None
        
        # We need to scroll and find sections
        # Sections are usually <ytd-item-section-renderer>
        
        # Basic loop:
        # 1. Get all header elements (Dates)
        # 2. Check the last one.
        # 3. If last one is still > Start Date, Scroll more.
        # 4. If last one < Start Date, we have gone far enough.
        
        reached_end = False
        
        # Keep track of processed section indices to avoid double counting if possible,
        # but simpler to just re-scan or grab everything and filter.
        # Dynamic pages are tricky. 
        # Strategy: Parse all visible, add to list, remove duplicates by ID/Link later. 
        # Then, decide if we need more.
        
        processed_links_map = {} # Map Link -> Index in collected_videos

        loop_count = 0
        max_loops = 50
        
        while not reached_end:
            loop_count += 1
            if loop_count > max_loops:
                print("Max loops reached. Stopping.")
                break
                
            # Find all section headers
            sections = driver.find_elements(By.TAG_NAME, "ytd-item-section-renderer")
            
            # If no sections, maybe page loading or empty
            if not sections:
                print(f"No sections found. Current URL: {driver.current_url}")
                time.sleep(2)
                continue

            last_section_date_val = None

            for section in sections:
                try:
                    header_el = section.find_element(By.ID, "header").text
                    # header text ex: "Today", "Yesterday", "Sunday", "Jan 25"
                    
                    section_date = parse_relative_date(header_el)
                    print(f"  Found section header: '{header_el}' -> Parsed: {section_date}")
                    if not section_date:
                        continue
                        
                    last_section_date_val = section_date

                    # Case 1: Too New
                    if section_date > end_date:
                        continue
                    
                    # Case 2: Too Old
                    if section_date < start_date:
                        reached_end = True
                        break # Stop processing sections

                    # Case 3: In Range
                    # Extract videos from this section
                    # Case 3: In Range
                    # Extract videos from this section
                    # Robust approach: Find links by URL pattern
                    # Standard videos: /watch?v=...
                    # Shorts: /shorts/...
                    # Refined selector to target only the main video title
                    video_elements = section.find_elements(By.CSS_SELECTOR, "a#video-title")
                    
                    for title_el in video_elements:
                        try:
                            title = title_el.text.strip()
                            raw_link = title_el.get_attribute("href")
                            
                            if not title or not raw_link:
                                continue

                            # Clean up URL (remove query params)
                            if "/watch?v=" in raw_link:
                                vid_id = raw_link.split("v=")[1].split("&")[0]
                                link = f"https://www.youtube.com/watch?v={vid_id}"
                            elif "/shorts/" in raw_link:
                                vid_id = raw_link.split("/shorts/")[1].split("?")[0]
                                link = f"https://www.youtube.com/shorts/{vid_id}"
                            else:
                                link = raw_link
                            
                            # Deduplicate
                            if link in processed_links_map:
                                existing_idx = processed_links_map[link]
                                existing_title = collected_videos[existing_idx]['Title']
                                if len(title) > len(existing_title):
                                    collected_videos[existing_idx]['Title'] = title
                            else:
                                processed_links_map[link] = len(collected_videos)
                                collected_videos.append({
                                    "Date": section_date,
                                    "Title": title,
                                    "Link": link
                                })
                                count_found += 1

                        except Exception as e:
                            pass
                    
                    print(f"    Found {count_found} video items in this section.")

                except Exception as e:
                    # Stale element etc
                    continue
            
            if reached_end:
                break
                
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2) # Wait for content load
            
            # Safety break if we scroll too much or no progress?
            # For now, trust the date check.
            
            # Optimization: If the last section on screen is already older than start_date, we are done.
            if last_section_date_val and last_section_date_val < start_date:
                 reached_end = True

        print(f"Scraping complete. Found {len(collected_videos)} videos.")
        
        # Write to CSV
        output_file = "youtube_history.csv"
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Title', 'Link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for video in collected_videos:
                writer.writerow(video)
                
        print(f"Saved to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_history()
