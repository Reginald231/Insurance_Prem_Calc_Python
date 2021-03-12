from selenium import webdriver
from selenium.webdriver.support.select import Select
from spreadsheetMaker import SpreadSheetMaker
import time
import csv
import tqdm


def load_preferences():

    my_lines = []  # Declare an empty list
    with open('preferences.txt', 'rt') as my_file:  # Open lorem.txt for reading text.
        for line in my_file:  # For each line of text,
            if '#' in line or line == '\n':
                continue
            else:
                my_lines.append(line.replace("\n", ""))  # add that line to the list.
    return my_lines


class HomeOwner:
    preferences = {
        'Year_Built': None,
        'Insured_Value': None,
        'Policy_Start_Date': None,
        'State': None,
        'Path': None,
        'Preferred_Spreadsheet_Name': None
    }
    zip_codes = list()
    data = list()

    def __init__(self):
        items = load_preferences()
        for key in self.preferences:
            for item in items:
                item = item.split('=')
                if item[0] in key:  # Left side of split is attribute
                    self.preferences[key] = item[1]  # Right side of split is value of attribute

        self.load_zips()

    def build_spreadsheet(self):
        spreadsheet = SpreadSheetMaker(data=self.data, preferred_sheet_name=self.preferences['Preferred_Spreadsheet_Name'])
        spreadsheet.build_spreadsheet()

    def get_desc(self):
        for key in self.preferences:
            print(f"{key}: {self.preferences[key]}")

    def load_zips(self):
        with open('zip_database.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            for row in csv_reader:
                code_type = row[1]
                state = row[3]
                decommissioned = row[8]

                # Filtering through bad zips
                if code_type != 'PO BOX' and state == 'CA' and decommissioned == 'false':
                    zipcode = int(row[0])
                    self.zip_codes.append(zipcode)
                    line_count += 1

            print(f'{line_count} usable zip codes discovered.\n')

    def enter_zip(self, driver, zip):
        zipcode_box = driver.find_element_by_id("zipcode")
        zipcode_box.clear()
        zipcode_box.send_keys(zip)

        get_started = driver.find_element_by_class_name("btn.btn-block.btn-primary.ng-binding.ng-scope")
        get_started.click()

        yearbuilt_box = driver.find_element_by_id("yearbuilt")
        yearbuilt_box.clear()
        yearbuilt_box.send_keys("1995")

    def start_to_state(self, driver, DROPDOWN_DEFAULT, STREET_DEFAULT):
        start_date = driver.find_element_by_id("startdate")
        start_date.clear()
        start_date.click()
        start_date.send_keys(self.preferences['Policy_Start_Date'])

        insurance_dropdown = driver.find_element_by_id("participatingInsurer")
        insurance_dropdown.click()
        insurance_dropdown = Select(driver.find_element_by_id("participatingInsurer"))
        insurance_dropdown.select_by_visible_text(DROPDOWN_DEFAULT)

        street = driver.find_element_by_id("street")
        street.clear()
        street.send_keys(STREET_DEFAULT)

        state_text_box = driver.find_element_by_id("state")
        state_text_box.clear()
        state_text_box.send_keys(self.preferences['State'])  # May want to read this from a text file later.

    def get_annual_premiums(self):
        DROPDOWN_DEFAULT = "Other"
        STREET_DEFAULT = 1

        options = webdriver.ChromeOptions()
        options.add_argument('headless')  # Running program without the use of the Google Chrome UI.
        driver = webdriver.Chrome(self.preferences['Path'], options=options)

        # driver = webdriver.Chrome(self.preferences['Path'])
        driver.implicitly_wait(10)
        driver.delete_all_cookies()
        driver.get("https://calc.earthquakeauthority.com/app/")

        i = 0
        backtrack = False
        pbar = tqdm.tqdm(total=len(self.zip_codes))
        while i < len(self.zip_codes):
            # if i == 10:   # A conditional for quicker testing.
            #     break
            if backtrack is False:
                home_coverage = driver.find_element_by_class_name("btn.cea-policy-btn.ng-binding")
                home_coverage.click()
                self.start_to_state(driver=driver, DROPDOWN_DEFAULT=DROPDOWN_DEFAULT, STREET_DEFAULT=STREET_DEFAULT)

            else:
                backtrack = False
                self.start_to_state(driver=driver, DROPDOWN_DEFAULT=DROPDOWN_DEFAULT, STREET_DEFAULT=STREET_DEFAULT)

            try:
                self.enter_zip(driver=driver, zip=self.zip_codes[i])

            except:
                print("Invalid zip discovered. Trying next zip.")
                backtrack = True
                i += 1
                pbar.update(1)
                continue

            insuredvalue_box = driver.find_element_by_id("insuredvalue")
            insuredvalue_box.clear()
            insuredvalue_box.send_keys(self.preferences['Insured_Value'])

            stories = Select(driver.find_element_by_id("numberofstories"))
            stories.select_by_visible_text("Greater than one")

            foundation = Select(driver.find_element_by_id("foundationtype"))
            foundation.select_by_visible_text(DROPDOWN_DEFAULT)

            roof = Select(driver.find_element_by_id("rooftype"))
            roof.select_by_visible_text(DROPDOWN_DEFAULT)

            get_estimate = driver.find_element_by_class_name("btn.btn-block.btn-primary.single-button.ng-binding")
            get_estimate.click()

            time.sleep(1)
            annual_premium = driver.find_element_by_class_name("gauge-subtitle.ng-binding.ng-scope").text
            annual_premium = float(annual_premium.replace("Annual Premium: $", ''))

            start_over = driver.find_element_by_class_name("btn.btn-accent.btn-block.ng-binding")
            start_over.click()
            self.data.append({'Zip Code': self.zip_codes[i], 'Annual Premium': annual_premium})
            i += 1
            pbar.update(1)
        driver.delete_all_cookies()
        driver.quit()