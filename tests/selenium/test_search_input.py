from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_search_input():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)

        search_box = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[placeholder='Search venues...']")
            )
        )

        search_box.clear()
        search_box.send_keys("Scotia")

        entered_value = search_box.get_attribute("value")
        assert entered_value == "Scotia"

        print("Search input test passed.")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_search_input()