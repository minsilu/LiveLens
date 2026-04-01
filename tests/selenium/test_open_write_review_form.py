from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_write_review_form_can_be_opened_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled to review section")

        write_review_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Write a Review')]")
            )
        )
        write_review_button.click()
        print("Step 3: clicked Write a Review button")

        review_form_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Write a Review')]")
            )
        )
        print("Step 4: found review form header")

        event_selection_label = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Which event did you attend?')]")
            )
        )
        print("Step 5: found event selection field")

        section_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Select section')]")
            )
        )
        print("Step 6: found section input")

        row_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Select row')]")
            )
        )
        print("Step 7: found row input")

        assert review_form_header.is_displayed(), "Review form header is not visible."
        assert event_selection_label.is_displayed(), "Event selection field is not visible."
        assert section_input.is_displayed(), "Section input is not visible."
        assert row_input.is_displayed(), "Row input is not visible."

        print("PASS: Write a review form can be opened on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_write_review_form_can_be_opened_on_venue_details_page()