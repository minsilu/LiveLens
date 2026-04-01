from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_sign_in_and_sign_up_buttons_are_displayed_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        sign_in_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Sign in')]")
            )
        )
        print("Step 2: found Sign in button")

        sign_up_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Sign up')]")
            )
        )
        print("Step 3: found Sign up button")

        assert sign_in_button.is_displayed(), "Sign in button is not visible."
        assert sign_up_button.is_displayed(), "Sign up button is not visible."

        print("PASS: Sign in and Sign up buttons are displayed on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_sign_in_and_sign_up_buttons_are_displayed_on_venue_details_page()