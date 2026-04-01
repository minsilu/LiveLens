from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_review_sort_dropdown_can_be_opened_and_updated():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled to review section")

        sort_dropdown = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Sort by: Relevance')]")
            )
        )
        sort_dropdown.click()
        print("Step 3: opened review sort dropdown")

        most_recent_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Most Recent')]")
            )
        )
        most_recent_option.click()
        print("Step 4: selected Most Recent")

        updated_sort = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Sort by: Most Recent')]")
            )
        )

        assert updated_sort.is_displayed(), "Updated review sort option is not visible."

        print("PASS: Review sort dropdown can be opened and updated on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_review_sort_dropdown_can_be_opened_and_updated()