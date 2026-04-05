from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_add_photos_button_can_be_used_in_write_review_form():
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
        driver.execute_script("arguments[0].click();", write_review_button)
        print("Step 3: opened write review form")

        add_photos_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Add Photos')]")
            )
        )
        print("Step 4: found Add Photos button")

        driver.execute_script("arguments[0].click();", add_photos_button)
        print("Step 5: clicked Add Photos button")

        file_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file']")
            )
        )
        print("Step 6: found file input")

        assert add_photos_button.is_displayed(), "Add Photos button is not visible."
        assert file_input.is_displayed() or file_input.get_attribute("type") == "file", "File input was not found."

        print("PASS: Add Photos button can be used in the write review form.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_add_photos_button_can_be_used_in_write_review_form()