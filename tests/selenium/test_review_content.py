from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_review_content_is_displayed_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080")

        view_details_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'View Details')] | //a[contains(., 'View Details')]")
            )
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_details_button)

        try:
            view_details_button.click()
        except:
            driver.execute_script("arguments[0].click();", view_details_button)

        wait.until(EC.url_contains("/venue/"))
        print("Step 1: entered venue details page")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled down to reviews")

        reviewer_name = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Verified Attendee')]")
            )
        )
        print("Step 3: found reviewer name")

        review_text = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'The visual experience')]")
            )
        )
        print("Step 4: found review text")

        review_date = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), '2025')]")
            )
        )
        print("Step 5: found review date")

        assert reviewer_name.is_displayed(), "Reviewer name is not visible."
        assert review_text.is_displayed(), "Review text is not visible."
        assert review_date.is_displayed(), "Review date is not visible."

        print("PASS: Review content is displayed on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_review_content_is_displayed_on_venue_details_page()