# Selenium Tests

## Prerequisites
- Install Python dependencies:
  - `pip3 install selenium`
- Start the frontend locally:
  - `cd frontend`
  - `npm run dev`
- Make sure the backend is also running if you want to test search results, sorting behavior, or other API-driven features.
  - `uvicorn api.main:app --reload`
  - `http://127.0.0.1:8000/docs`


## Run the test
From the project root, run each test file individually:

```bash
python3 tests/selenium/test_homepage.py
python3 tests/selenium/test_discover_section.py
python3 tests/selenium/test_search_input.py
python3 tests/selenium/test_sort_dropdown.py
python3 tests/selenium/test_venue_details_navigation.py
python3 tests/selenium/test_reviews_section.py
python3 tests/selenium/test_review_content.py
python3 tests/selenium/test_review_sort_dropdown.py
python3 tests/selenium/test_review_section_filter.py
python3 tests/selenium/test_write_review_button.py
python3 tests/selenium/test_open_write_review_form.py
python3 tests/selenium/test_3d_view_open.py
python3 tests/selenium/test_chat_widget.py
python3 tests/selenium/test_auth_buttons.py
python3 tests/selenium/test_post_review.py
```

## Current test coverage

These Selenium tests currently verify:
 - the homepage loads successfully
 - the discover section is rendered
 - the venue search input accepts user input
 - the sort dropdown can be opened and updated
 - the view details button can be used to open a venue details page
 - the review section is displayed on the venue details page(need click the "view detail" button)
 - the review content is displayed on the venue details page
 - the review sort dropdown can be opened and updated on the venue details page
 - the review section filter dropdown can be opened and updated on the venue details page
 - the write a review button is displayed on the venue details page
 - the write a review dialog can be opened from the venue details page
 - the 3D venue view can be opened from the venue details page
 - the chat widget can be opened on the venue details page
 - the sign in and sign up buttons are displayed on the venue details page
 - posting a review requires the user to be logged in


## Notes
- The frontend runs locally at http://localhost:8080
- Some tests depend on backend data being available
- Run all tests from the project root directory
- Most venue-details-related tests use a direct venue URL to avoid flaky navigation during repeated runs