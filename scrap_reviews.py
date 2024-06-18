
from flask import Flask, request, render_template, jsonify, send_from_directory
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains



def scrape_review(url):
    driver = webdriver.Chrome()
    driver.maximize_window()
    try:
        driver.get(url)
        time.sleep(3)  
        
        review_data = []
        
        reviews = driver.find_elements(By.XPATH, "//div[@data-testid='pdp-reviews-modal-scrollable-panel']/div")
        
        for i, review in enumerate(reviews, start=1):
            review_dict = {
                'review_link': url,
                'reviewer_name': None,
                'reviewer_profile_link': None,
                'info': None,
                'rating_comment': None,
                'rating_extra': None
            }
            
            try:
                reviewer_name_tag = review.find_element(By.XPATH, f"//div[@data-testid='pdp-reviews-modal-scrollable-panel']/div[{i}]/div/section/div/div/h2")
                reviewer_name = reviewer_name_tag.text if reviewer_name_tag else 'None'
                review_dict['reviewer_name'] = reviewer_name
            except Exception as e:
                print("User name not fetched", e)
                
            try:
                rating_extra_tag = review.find_element(By.XPATH, f"//div[@data-testid='pdp-reviews-modal-scrollable-panel']/div[{i}]/div/section/div/div/div")
                rating_extra = rating_extra_tag.text if rating_extra_tag else 'None'
                review_dict['rating_extra'] = rating_extra
            except Exception as e:
                print("No extra rating")
                
            try:
                profile_link_elem = driver.find_element(By.XPATH, f"//a[@aria-label='{review_dict['reviewer_name']}']")
                review_dict['reviewer_profile_link'] = profile_link_elem.get_attribute('href')
            except:
                print('Reviewer profile link not found')
                
            try:
                parent_div = review.find_element(By.XPATH, './/div[@class="s78n3tv atm_c8_1w0928g atm_g3_1dd5bz5 atm_cs_9dzvea atm_9s_1txwivl atm_h_1h6ojuz dir dir-ltr"]')
                full_text = parent_div.get_attribute('textContent').strip()
                info_text = full_text.split('\n')[-1].strip()
                review_dict['info'] = info_text
            except:
                print("Review time not fetched")
                
            try:
                rating_comment_tag = review.find_element(By.XPATH, f"(.//div[@class='r1bctolv atm_c8_1sjzizj atm_g3_1dgusqm atm_26_lfmit2_13uojos atm_5j_1y44olf_13uojos atm_l8_1s2714j_13uojos dir dir-ltr']/div/span/span)")
                rating_comment = rating_comment_tag.text if rating_comment_tag else 'N/A'
                review_dict['rating_comment'] = rating_comment
            except Exception as e:
                print("Rating comment not fetched", e)
                
            review_data.append(review_dict)

        driver.quit()
        return review_data

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        driver.quit()
        return []

def scrape_reviews_for_listings(listing_links):
    all_reviews = []
    for url in listing_links:
        reviews = scrape_review(url)
        all_reviews.extend(reviews)
    return pd.DataFrame(all_reviews)