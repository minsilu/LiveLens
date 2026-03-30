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
From the project root:

```bash
python3 tests/selenium/test_homepage.py
python3 tests/selenium/test_discover_section.py
python3 tests/selenium/test_search_input.py
python3 tests/selenium/test_sort_dropdown.py
```

## Current test coverage

These Selenium tests currently verify:
 - the homepage loads successfully
 - the discover section is rendered
 - the venue search input accepts user input
 - the sort dropdown can be opened and updated

## Notes
- The frontend runs locally at http://localhost:8080
- Some tests depend on backend data being available
- Run tests from the project root directory