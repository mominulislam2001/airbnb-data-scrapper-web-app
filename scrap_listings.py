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


def scrap_airbnb_listing(location_list, xpath_filename):
    main_link = "https://www.airbnb.com/s/"
    xpaths = load_json(xpath_filename)
    driver = webdriver.Chrome()
    driver.maximize_window()
    total_dict = []
    for location in location_list:
        main_link = f"https://www.airbnb.com/s/{location}/homes"
        driver.get(main_link)
        time.sleep(2)
        for i in range(1, 19):
            dict_ = {"location": location, "listing_link": None}
            try:
                listing_link = driver.find_element('xpath', f"{xpaths['apartment_link_xpath']}[{i}]")
                dict_['listing_link'] = listing_link.get_attribute('href')
                total_dict.append(dict_)
            except:
                break
            try:
                result_count_string = driver.find_element('xpath', xpaths['result_count_xpath']).text
                result_count = result_count_maker(result_count_string)
            except:
                continue
            page_count = result_count // 18
            if page_count >= 15:
                page_count = 15
            while page_count > 0:
                try:
                    next_page_link = driver.find_element('xpath', xpaths['next_page_xpath'])
                    next_page_link.click()
                    time.sleep(2)
                    for i in range(1, 19):
                        dict_ = {"location": location, "listing_link": None}
                        try:
                            listing_link = driver.find_element('xpath', f"{xpaths['apartment_link_xpath']}[{i}]")
                            dict_['listing_link'] = listing_link.get_attribute('href')
                            total_dict.append(dict_)
                        except:
                            break
                except:
                    break
                page_count -= 1
    driver.quit()
    return pd.DataFrame(total_dict)