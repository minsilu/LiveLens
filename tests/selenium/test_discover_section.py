from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_discover_section():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)

        heading = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(., 'Discover Music Venues')]")
            )
        )
        assert heading.is_displayed()

        search_box = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[placeholder='Search venues...']")
            )
        )
        assert search_box.is_displayed()

        sort_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(., 'Sort by: Relevance')]")
            )
        )
        assert sort_button.is_displayed()

        print("Discover section test passed.")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_discover_section()