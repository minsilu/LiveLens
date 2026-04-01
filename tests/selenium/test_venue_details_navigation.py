from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_click_view_details_navigates_to_venue_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("http://localhost:8080")

        view_details_buttons = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//button[contains(., 'View Details')] | //a[contains(., 'View Details')]")
            )
        )

        assert len(view_details_buttons) > 0, "No 'View Details' button found on homepage."

        old_url = driver.current_url

        first_button = view_details_buttons[0]
        wait.until(EC.element_to_be_clickable(first_button))
        first_button.click()

        wait.until(lambda d: d.current_url != old_url)

        new_url = driver.current_url
        assert new_url != old_url, "Clicking 'View Details' did not navigate to a new page."

        assert (
            "venue" in new_url.lower()
            or "detail" in new_url.lower()
            or "/venues/" in new_url.lower()
        ), f"Unexpected details page URL: {new_url}"

        print("PASS: View Details navigation works.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_click_view_details_navigates_to_venue_page()