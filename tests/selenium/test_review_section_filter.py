from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_review_section_filter_dropdown_can_be_opened_and_updated():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.45);")
        print("Step 2: scrolled to review section")

        section_dropdown = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(normalize-space(), 'Section: All')]")
            )
        )
        section_dropdown.click()
        print("Step 3: opened section filter dropdown")

        section_one_option = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space()='1']")
            )
        )
        section_one_option.click()
        print("Step 4: selected section 1")

        updated_filter = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Section: 1')]")
            )
        )

        assert updated_filter.is_displayed(), "Updated section filter is not visible."

        print("PASS: Review section filter dropdown can be opened and updated on the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_review_section_filter_dropdown_can_be_opened_and_updated()