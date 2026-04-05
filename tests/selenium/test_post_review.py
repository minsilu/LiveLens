import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_posting_a_review_requires_login():
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

        post_review_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Post Review')]")
            )
        )
        driver.execute_script("arguments[0].click();", post_review_button)
        print("Step 4: clicked Post Review")

        alert = wait.until(EC.alert_is_present())
        alert_text = alert.text
        print(f"Step 5: alert appeared -> {alert_text}")

        assert "log in" in alert_text.lower(), f"Unexpected alert text: {alert_text}"

        alert.accept()
        print("PASS: Posting a review requires the user to be logged in.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_posting_a_review_requires_login()