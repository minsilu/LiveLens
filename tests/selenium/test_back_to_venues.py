from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_back_to_venues_link_can_be_used_on_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        back_link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Back to venues')]")
            )
        )
        print("Step 2: found Back to venues link")

        driver.execute_script("arguments[0].click();", back_link)
        print("Step 3: clicked Back to venues link")

        wait.until(lambda d: "/venue/" not in d.current_url)
        print("Step 4: navigated away from venue details page")

        current_url = driver.current_url
        assert "/venue/" not in current_url, f"Still on venue details page: {current_url}"

        print("PASS: Back to venues link can be used on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_back_to_venues_link_can_be_used_on_venue_details_page()