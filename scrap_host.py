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

def scrap_host(host_links, xpath_filename):
    xpaths = load_json(xpath_filename)
   
    total_host = []
    driver = webdriver.Chrome()
    driver.maximize_window()

    for host_link in host_links:
        host_dict = {
            "host_link": host_link,
            "host_name": None,
            "host_rating": None,
            "host_no_of_review": None,
            "host_hosting_duration": None,
            "host_no_of_listing": None,
            "host_listing_links": None,
            "host_about": None,
            "host_confirmed_information": None,
        }

        print(f"Fetching host details from: {host_link}")
        try:
            driver.get(host_link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            try:
                host_name_element = driver.find_element(By.XPATH, xpaths['host_name_xpath'])
                host_dict['host_name'] = host_name_element.text
            except:
                print("Host name not found")

            try:
                span_elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[@class='s1yopat4 atm_9s_1txwivl atm_ar_1bp4okc atm_cx_1lkvw50 atm_h_1y6m0gg atm_fc_1h6ojuz atm_cs_1fw03zg atm_c8_sz6sci atm_g3_17zsb9a atm_fr_kzfbxz dir dir-ltr']/span"))
                )
                for span in span_elements:
                    try:
                        data_testid = span.get_attribute('data-testid')
                        if data_testid in ['Reviews-stat-heading', 'Review-stat-heading']:
                            host_dict['host_no_of_review'] = span.text
                        elif data_testid in ['Years hosting-stat-heading', 'Year hosting-stat-heading', 'Months hosting-stat-heading', 'Month hosting-stat-heading']:
                            duration = span.text + (" years" if "Year" in data_testid else " months")
                            host_dict['host_hosting_duration'] = duration
                    except:
                        pass
            except:
                print("Review count or hosting duration not found")

            try:
                host_rating_element = driver.find_element(By.XPATH, xpaths['host_ratings_xpath'])
                host_dict['host_rating'] = host_rating_element.text
            except:
                print("Host rating not fetched")

            try:
                host_listing_links_elements = driver.find_elements(By.XPATH, xpaths['host_listing_link_xpath'])
                host_listing_links = [listing.get_attribute('href') for listing in host_listing_links_elements]
                host_dict['host_listing_links'] = host_listing_links
            except:
                print("Host listings not fetched")

            host_dict['host_no_of_listing'] = len(host_listing_links)

            try:
                host_confirmed_info_elements = driver.find_elements(By.XPATH, xpaths['host_confirmed_info_xpath'])
                host_confirmed_info_list = [elem.text for elem in host_confirmed_info_elements if elem.text]
                host_dict['host_confirmed_information'] = host_confirmed_info_list
            except:
                print("No more host confirmed info")

            try:
                div_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='dbk58ns atm_9s_1txwivl atm_ar_1bp4okc atm_cx_1od0ugv dir dir-ltr']"))
                )
                child_elements = div_element.find_elements(By.XPATH, "./*")
                all_about = ""
                for child in child_elements:
                    text = child.text
                    if text:
                        all_about += " " + text
                host_dict['host_about'] = all_about
            except:
                print("About not found")

            total_host.append(host_dict)

        except Exception as e:
            print(f"Fetching host details failed: {e}")

    driver.quit()
    return pd.DataFrame(total_host)
