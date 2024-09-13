from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import time

# Path to the ChromeDriver (update this with your own location)
CHROME_DRIVER_PATH = r"C:\Users\DELL\node_modules\chromedriver\lib\chromedriver\chromedriver.exe"

# Headless option setup
def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model (optional)
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems in Docker (optional)
    return chrome_options

# Function to scrape the main page for event links
def get_event_links(main_url):
    # Start a new Chrome session in headless mode
    service = Service(CHROME_DRIVER_PATH)
    options = get_chrome_options()
    driver = webdriver.Chrome(service=service, options=options)

    # Load the main events page
    driver.get(main_url)

    # Wait for the page to fully load and the event links to be present
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'events-listing-item')))
    except:
        print("Event links not found")
        driver.quit()
        return []

    # Find all event links
    events = driver.find_elements(By.CSS_SELECTOR, 'div.text-wrapper h3 a')
    event_links = [event.get_attribute('href') for event in events]

    driver.quit()
    return event_links

# Function to check if an individual event page mentions food by scanning the entire page
def check_event_for_food(event_url):
    service = Service(CHROME_DRIVER_PATH)
    options = get_chrome_options()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the event page
        driver.get(event_url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # Get the entire page's text
        page_text = driver.page_source.lower()

        # Keywords for food
        food_keywords = ['food', 'refreshments', 'lunch', 'dinner', 'breakfast', 'meal', 'snacks']

        # Check if any food-related keywords are in the page source
        if any(keyword in page_text for keyword in food_keywords):
            return event_url  # Return the URL if food is mentioned

    except Exception as e:
        print(f"Error scraping {event_url}: {e}")

    finally:
        driver.quit()

    return None

# Main function to scrape events with food in parallel
def scrape_events_with_food(main_url):
    # Get event links from the main page
    event_links = get_event_links(main_url)

    # Use ThreadPoolExecutor to check event pages concurrently
    food_events = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all event URLs to be checked concurrently
        futures = [executor.submit(check_event_for_food, event_link) for event_link in event_links]

        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                food_events.append(result)

    return food_events

# Run the script
if __name__ == "__main__":
    main_url = "https://calendar.syracuse.edu/events/"  # Syracuse University events page
    start_time = time.time()
    
    food_events = scrape_events_with_food(main_url)

    if food_events:
        print("Events that serve food:")
        for event in food_events:
            print(event)
    else:
        print("No food-related events found.")
    
    print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
