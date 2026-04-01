import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains


def force_click(driver, wait, xpath, step_name="element"):
    element = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(1)

    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()
    except:
        try:
            ActionChains(driver).move_to_element(element).pause(0.5).click().perform()
        except:
            driver.execute_script("arguments[0].click();", element)

    print(f"Clicked: {step_name}")
    return element


def test_3d_venue_view_can_be_opened_from_venue_details_page():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("http://localhost:8080/venue/6c74e3a3-9300-4e7a-8d33-31b472e9e7fc")
        print("Step 1: opened venue details page directly")

        wait.until(EC.url_contains("/venue/"))
        time.sleep(2)

        force_click(
            driver,
            wait,
            "//*[contains(normalize-space(), '3D View')]",
            "3D View button"
        )

        time.sleep(2)

        three_d_header = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), '3D Venue View')]")
            )
        )
        print("Step 2: found 3D Venue View header")

        interactive_text = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Interactive 3D View')]")
            )
        )
        print("Step 3: found Interactive 3D View text")

        explore_seats_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(), 'Explore Seats')]")
            )
        )
        print("Step 4: found Explore Seats button")

        assert three_d_header.is_displayed(), "3D Venue View header is not visible."
        assert interactive_text.is_displayed(), "Interactive 3D View text is not visible."
        assert explore_seats_button.is_displayed(), "Explore Seats button is not visible."

        print("PASS: 3D venue view can be opened from the venue details page.")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_3d_venue_view_can_be_opened_from_venue_details_page()