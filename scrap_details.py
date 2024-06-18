from flask import Flask, request, render_template, jsonify, send_from_directory
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains
from helper import result_count_maker, load_json

def airbnb_data_scrap(listing_links, locations, xpath_filename):
    total_dict = []
    xpaths_dict = load_json(xpath_filename)
   
    driver = webdriver.Chrome()
    driver.maximize_window()

    for listing, location in zip(listing_links, locations):
        dict_ = {
            "listing_link": listing,
            "searched_location": location,
            "title_bed_bats_review": None,
            "price_per_night": None,
            "review_count": None,
            "review_count_link": None,
            "host_link": None,
            "host_response_rate": None,
            "listing_description": None,
            "cleanliness_ratings": None,
            "accuracy_ratings": None,
            "check-in_ratings": None,
            "communication_ratings": None,
            "location_ratings": None,
            "value_ratings": None,
            "google_map_location_link": None
        }

        try:
            driver.get(listing)
            time.sleep(2)
            
            try:
                modal_close_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Close"]'))
                )
                modal_close_button.click()
                print("Modal closed")
            except:
                print("No modal found")

            time.sleep(2)

            try:
                title_bed_bats_review = driver.find_element('xpath', xpaths_dict['title_bed_bats_review'])
                title_bed_bats_review = title_bed_bats_review.get_attribute('content')
                dict_["title_bed_bats_review"] = title_bed_bats_review
            except:
                print("No Meta")
                
            try:
                span_elements = driver.find_elements(By.CLASS_NAME, '_1y74zjx')
                k = 0
                for span in span_elements:
                    if k == 1:
                        dict_['price_per_night'] = span.text
                    k += 1
            except:
                print("Price Not Found")
            
            try:
                review_count_element = driver.find_element("xpath", xpaths_dict['review_count_xpath'])
                review_count = review_count_element.text
                review_count_link = review_count_element.get_attribute('href')
                dict_['review_count'] = review_count
                dict_['review_count_link'] = review_count_link
            except:
                print("Review count not found")

            try:
                host_link_element = driver.find_element('xpath', xpaths_dict['host_link_Xpath'])
                host_link = host_link_element.get_attribute('href')
                dict_['host_link'] = host_link
            except:
                print("Host not found")

            try:
                host_response_rate = driver.find_element('xpath', xpaths_dict["response_rate_Xpath"])
                dict_['host_response_rate'] = host_response_rate.text
            except:
                print("Host response rate not found")

            for i in range(1, 7):
                try:
                    ind_ratings = driver.find_element('xpath', f"({xpaths_dict['ind_rev_xpath']})[{i}]")
                    if i == 1:
                        dict_['cleanliness_ratings'] = ind_ratings.text
                    elif i == 2:
                        dict_['accuracy_ratings'] = ind_ratings.text
                    elif i == 3:
                        dict_['check-in_ratings'] = ind_ratings.text
                    elif i == 4:
                        dict_['communication_ratings'] = ind_ratings.text
                    elif i == 5:
                        dict_['location_ratings'] = ind_ratings.text
                    elif i == 6:
                        dict_['value_ratings'] = ind_ratings.text
                except:
                    pass

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='_1ctob5m']"))
            )
            
            try:
                actions = ActionChains(driver)
                actions.move_to_element(element).perform()
                time.sleep(3)
            except:
                print("Not able to scroll")
            
            try:
                google_map_location = driver.find_element('xpath', xpaths_dict['lat-lon-link'])
                google_map_location_link = google_map_location.get_attribute('href')
                dict_['google_map_location_link'] = google_map_location_link
            except:
                print("No Google map link")

            element2 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpaths_dict['facilities_button_xpath']))
            )
            
            try:
                actions = ActionChains(driver)
                actions.move_to_element(element2).perform()
                time.sleep(2)
            except:
                print("Not able to scroll up")
            
            facilities_list = []
            try:
                show_all_facilities = driver.find_element('xpath', xpaths_dict['facilities_button_xpath'])
                show_all_facilities.click()
                for i in range(1, 100):
                    try:
                        facility = driver.find_element('xpath', f"({xpaths_dict['facilities_xpath']})[{i}]")
                        facilities_list.append(facility.text)
                    except:
                        break
                
                dict_["facilities"] = facilities_list

                try:
                    modal_close_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Close"]'))
                    )
                    modal_close_button.click()
                    print("Facilities closed")
                except:
                    print("Facilities not closed, sorry")
            except:
                print("Facilities not found")
            
            try:
                button_element = driver.find_element(By.XPATH, xpaths_dict['description_show_all_Xpath'])
                button_element.click()
                time.sleep(1)
                description_section_element = driver.find_element(By.XPATH, xpaths_dict['description_xpath'])
                description_text = description_section_element.text
                dict_['listing_description'] = description_text
                time.sleep(1)
            except:
                try:
                    description2_section_element = driver.find_element('xpath', xpaths_dict['description2_xpath'])
                    dict_['listing_description'] = description2_section_element.text
                except:
                    print("Show all description button not found")

            total_dict.append(dict_)
        except:
            pass

    driver.quit()
    return pd.DataFrame(total_dict)