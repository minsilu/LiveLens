from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

def test_sort_dropdown():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:8080")
        wait = WebDriverWait(driver, 10)

        sort_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Sort by:')]")
            )
        )
        sort_button.click()

        rating_option = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'absolute')]//*[normalize-space()='Rating']")
            )
        )

        ActionChains(driver).move_to_element(rating_option).click().perform()

        updated_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(., 'Sort by: Rating')]")
            )
        )
        assert updated_button.is_displayed()

        print("Sort dropdown test passed.")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_sort_dropdown()