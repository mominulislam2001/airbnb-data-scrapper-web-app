from flask import Flask, request, render_template, jsonify, send_from_directory
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains



from scrap_host import scrap_host
from scrap_details import airbnb_data_scrap
from scrap_listings import scrap_airbnb_listing
from scrap_reviews import scrape_reviews_for_listings,scrape_review

app = Flask(__name__)




@app.route('/')
def index():
    summary = {
        "total_listings": 0,
        "new_listings": 0,
        "total_hosts": 0,
        "total_reviews": 0
    }
    
    listings_csv_path = os.path.join('output', 'listing.csv')
    detailed_csv_path = os.path.join('output', 'detailed_listings.csv')
    host_csv_path = os.path.join('output', 'host_details.csv')
    reviews_csv_path = os.path.join('output', 'reviews.csv')
    
    if os.path.exists(listings_csv_path):
        listings_df = pd.read_csv(listings_csv_path)
        summary["total_listings"] = len(listings_df)
    
    if os.path.exists(detailed_csv_path):
        detailed_df = pd.read_csv(detailed_csv_path)
        summary["total_listings"] = len(detailed_df)
        summary["new_listings"] = len(detailed_df)
    
    if os.path.exists(host_csv_path):
        host_df = pd.read_csv(host_csv_path)
        summary["total_hosts"] = len(host_df)
    
    if os.path.exists(reviews_csv_path):
        reviews_df = pd.read_csv(reviews_csv_path)
        summary["total_reviews"] = len(reviews_df)
    
    return render_template('index.html', **summary)


# Add this route to serve the files
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(directory='output', path=filename)

# Update your routes to return the filename only
@app.route('/scrape', methods=['POST'])
def scrape():
    
    locations = request.form.get('locations').split(',')
    xpath_filename = request.form.get('xpath_filename')
    df = scrap_airbnb_listing(locations, xpath_filename)
    csv_file = 'listing.csv'
    os.makedirs('output', exist_ok=True)
    df.to_csv(os.path.join('output', csv_file), index=False)
    
    return render_template('message.html', message="Scraping completed successfully", file=csv_file)

@app.route('/scrape_details', methods=['POST'])
def scrape_details():
    listings_df = pd.read_csv(os.path.join('output', 'listing.csv'))
    listing_links = listings_df['listing_link'].tolist()
    locations = listings_df['location'].tolist()
    xpath_filename = request.form.get('xpath_filename')
    detailed_df = airbnb_data_scrap(listing_links, locations, xpath_filename)
    detailed_csv_file = 'detailed_listings.csv'
    os.makedirs('output', exist_ok=True)
    detailed_df.to_csv(os.path.join('output', detailed_csv_file), index=False)
    return render_template('message.html', message="Detailed scraping completed successfully", file=detailed_csv_file)

@app.route('/scrape_host', methods=['POST'])
def scrape_host():
    details_df = pd.read_csv(os.path.join('output', 'detailed_listings.csv'))
    host_links_non_null = details_df['host_link'].dropna()
    host_links_non_null_non_dup = host_links_non_null.drop_duplicates().to_list()
    xpath_filename = request.form.get('xpath_filename')
    host_df = scrap_host(host_links_non_null_non_dup, xpath_filename)
    host_csv_file = 'host_details.csv'
    os.makedirs('output', exist_ok=True)
    host_df.to_csv(os.path.join('output', host_csv_file), index=False)
    return render_template('message.html', message="Host scraping completed successfully", file=host_csv_file)

@app.route('/scrape_review', methods=['POST'])
def scrape_reviews_route():
    detailed_df = pd.read_csv(os.path.join('output', 'detailed_listings.csv'))
    detailed_df.dropna(subset='review_count_link', inplace=True)
    detailed_df['review_count'] = detailed_df['review_count'].str.strip(' reviews')
    detailed_df['review_count'] = detailed_df['review_count'].astype(int)
    detailed_df = detailed_df[detailed_df['review_count'] > 0]['review_count_link']
    
    host_review_links = detailed_df.tolist()
    reviews_df = scrape_reviews_for_listings(host_review_links)
    reviews_csv_file = 'reviews.csv'
    os.makedirs('output', exist_ok=True)
    reviews_df.to_csv(os.path.join('output', reviews_csv_file), index=False)
    return render_template('message.html', message="Review scraping completed successfully", file=reviews_csv_file)
@app.route('/scrape_all', methods=['POST'])
def scrape_all():
    # Step 1: Scrape listings
    locations = request.form.get('locations').split(',')
    xpath_filename = request.form.get('xpath_filename')
    new_listings_df = scrap_airbnb_listing(locations, xpath_filename)
    new_listings_csv_file = 'listing.csv'
    os.makedirs('output', exist_ok=True)
    
    listings_csv_path = os.path.join('output', new_listings_csv_file)
    if os.path.exists(listings_csv_path):
        existing_listings_df = pd.read_csv(listings_csv_path)
    else:
        existing_listings_df = pd.DataFrame()

    # Combine new listings with existing listings and remove duplicates
    combined_listings_df = pd.concat([existing_listings_df, new_listings_df]).drop_duplicates(subset='listing_link', keep='first')
    combined_listings_df.to_csv(listings_csv_path, index=False)
    
    # Get new listing links that are not in the existing listings
    new_listing_links = new_listings_df[~new_listings_df['listing_link'].isin(existing_listings_df['listing_link'])]

    # Step 2: Scrape detailed listings
    if not new_listing_links.empty:
        listing_links = new_listing_links['listing_link'].tolist()
        locations = new_listing_links['location'].tolist()
        detailed_df = airbnb_data_scrap(listing_links, locations, xpath_filename)
        detailed_csv_file = 'detailed_listings.csv'
        
        detailed_csv_path = os.path.join('output', detailed_csv_file)
        if os.path.exists(detailed_csv_path):
            existing_detailed_df = pd.read_csv(detailed_csv_path)
        else:
            existing_detailed_df = pd.DataFrame()

        # Combine new detailed listings with existing detailed listings and remove duplicates
        combined_detailed_df = pd.concat([existing_detailed_df, detailed_df]).drop_duplicates(subset='listing_link', keep='first')
        combined_detailed_df.to_csv(detailed_csv_path, index=False)

        # Step 3: Scrape host details
        host_links_non_null = detailed_df['host_link'].dropna().unique().tolist()
        if host_links_non_null:
            host_df = scrap_host(host_links_non_null, xpath_filename)
            host_csv_file = 'host_details.csv'
            
            host_csv_path = os.path.join('output', host_csv_file)
            if os.path.exists(host_csv_path):
                existing_host_df = pd.read_csv(host_csv_path)
            else:
                existing_host_df = pd.DataFrame()

            # Combine new host details with existing host details and remove duplicates
            combined_host_df = pd.concat([existing_host_df, host_df]).drop_duplicates(subset='host_link', keep='first')
            combined_host_df.to_csv(host_csv_path, index=False)

        # Step 4: Scrape reviews
        detailed_df.dropna(subset='review_count_link', inplace=True)
        detailed_df['review_count'] = detailed_df['review_count'].str.extract('(\d+)').astype(int)
        review_links = detailed_df[detailed_df['review_count'] > 0]['review_count_link'].tolist()
        if review_links:
            reviews_df = scrape_reviews_for_listings(review_links)
            reviews_csv_file = 'reviews.csv'
            
            reviews_csv_path = os.path.join('output', reviews_csv_file)
            if os.path.exists(reviews_csv_path):
                existing_reviews_df = pd.read_csv(reviews_csv_path)
            else:
                existing_reviews_df = pd.DataFrame()

            # Combine new reviews with existing reviews and remove duplicates
            combined_reviews_df = pd.concat([existing_reviews_df, reviews_df]).drop_duplicates(subset='review_link', keep='first')
            combined_reviews_df.to_csv(reviews_csv_path, index=False)
    
    return render_template('message.html', message="All scraping completed successfully",
                           file_list=[new_listings_csv_file, detailed_csv_file, host_csv_file, reviews_csv_file])


if __name__ == '__main__':
    app.run(debug=True)