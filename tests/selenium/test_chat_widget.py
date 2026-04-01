import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_chat_widget_can_be_opened_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))
        time.sleep(1)

        chat_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Chat')]")
            )
        )
        print("Step 2: found Chat button")

        driver.execute_script("arguments[0].click();", chat_button)
        print("Step 3: clicked Chat button")

        chat_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Chat with us')]")
            )
        )
        print("Step 4: found chat header")

        message_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@placeholder, 'Type a message')]")
            )
        )
        print("Step 5: found message input")

        send_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Send')]")
            )
        )
        print("Step 6: found Send button")

        assert chat_header.is_displayed(), "Chat widget header is not visible."
        assert message_input.is_displayed(), "Chat message input is not visible."
        assert send_button.is_displayed(), "Send button is not visible."

        print("PASS: Chat widget can be opened on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_chat_widget_can_be_opened_on_venue_details_page()