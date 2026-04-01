from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_reviews_section_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080")

        view_details_buttons = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//button[contains(., 'View Details')] | //a[contains(., 'View Details')]")
            )
        )

        assert len(view_details_buttons) > 0, "No 'View Details' button found."

        view_details_buttons[0].click()

        wait.until(EC.url_contains("/venue/"))
        print("Step 1: entered venue details page")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled down")

        reviews_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Customer Reviews')]")
            )
        )
        print("Step 3: found Customer Reviews header")

        write_review_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Write a Review')]")
            )
        )
        print("Step 4: found Write a Review button")

        assert reviews_header.is_displayed(), "Customer Reviews header is not visible."
        assert write_review_button.is_displayed(), "Write a Review button is not visible."

        print("PASS: Review section is displayed on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_reviews_section_on_venue_details_page()