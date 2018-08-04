from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

def get_Element(driver):
    """Find the "element" on the Chrome settings page."""
    return driver.find_element_by_css_selector('* /deep/ #clearBrowsingDataConfirm')


def clear_cache(driver, timeout=60):
    """Clear the cookies and cache for the ChromeDriver instance."""
    # navigate to the settings page
    driver.get('chrome://settings/clearBrowserData')

    # wait for the button to appear
    wait = WebDriverWait(driver, timeout)
    wait.until(get_Element)

    select = Select(driver.find_element_by_css_selector('* /deep/ select#dropdownMenu'))
    select.select_by_visible_text('All time')
    # click the button to clear the cache
    get_Element(driver).click()

    # wait for the button to be gone before returning
    wait.until_not(get_Element)


if __name__ == '__main__':
    _chrome_options = webdriver.ChromeOptions()
    _chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=_chrome_options)
    clear_cache(driver)
