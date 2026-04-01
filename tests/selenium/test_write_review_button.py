from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_write_review_button_is_displayed_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled to review section")

        write_review_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Write a Review')]")
            )
        )
        print("Step 3: found Write a Review button")

        assert write_review_button.is_displayed(), "Write a Review button is not visible."

        print("PASS: Write a Review button is displayed on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_write_review_button_is_displayed_on_venue_details_page()