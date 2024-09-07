import os
import time
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
from zipfile import ZipFile
import requests
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless")

IMAGE_TYPES = ['.jpg', '.png', '.jpeg', '.jfif', '.webp']

# Function to stream data
def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.03)

# Function to handle loading spinner
def loading_images():
    if st.session_state["loading"] == True:
        with st.spinner(f'Đang tìm ảnh  ...'):
            time.sleep(60)  

# Function to fetch images using Selenium
def fetch_images(url):
    all_images = []
    driver = webdriver.Chrome(service=Service(ChromeDriverManager("127.0.6533.89").install()), options=chrome_options)
    driver.get(url)

    while True:
        # Scroll dynamically to load more images if necessary
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait until new images are loaded
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'img'))
        )

        soup = BeautifulSoup(driver.page_source, 'lxml')

        images = soup.find_all('img')
        for image in images:
            img_url = image.get('src')
            img_caption = image.get('alt')
            if img_url is not None:
                img_url = urljoin(url, img_url)
                all_images.append({"url": img_url, "caption": img_caption})

        try:
            next_page_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='next']/a"))
            )
            driver.execute_script("arguments[0].click();", next_page_link)

        except:
            # No more pages to navigate to
            break

    driver.quit()
    return all_images

# Function to display images
def display_images(all_images):
    for image in all_images:
        st.image(image['url'], caption=f"{image['caption']}", width=500)
    st.session_state["loading"] = False


def download_images(all_images, output_format='PNG', resize_size=(613, 554)):
    folder_name = "downloaded_images"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    for i, image in enumerate(all_images):
        image_url = image['url']
        parsed_url = urlparse(image_url)
        image_extension = os.path.splitext(parsed_url.path)[1]  # Extract file extension
        image_name = f"image_{i + 1}{image_extension}"  # Give each image a unique name
        image_path = os.path.join(folder_name, image_name)

        # Download and save the image
        response = requests.get(image_url)
        image_content = BytesIO(response.content)

        # Open the image with Pillow
        img = Image.open(image_content)

        # Modify the image: Resize and convert to the desired format (PNG in this case)
        # img = img.resize(resize_size)  # Resize image
        img = img.convert('RGB')  # Convert to RGB format if necessary (for .png or other formats)

        # Save the modified image in the desired format (PNG in this case)
        img.save(image_path, output_format)

    return folder_name

def zip_images(folder_name):
    zip_filename = f"{folder_name}.zip"
    with ZipFile(zip_filename, "w") as zipf:
        for root, dirs, files in os.walk(folder_name):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    return zip_filename

# Main func ction
def main():
    if "loading" not in st.session_state:
        st.session_state["loading"] = True

    all_images = []

    with st.sidebar:
        url = st.text_input("URL").strip().lower()
        
        if url and st.button("Search", type="primary"):
            loading_images()
            all_images = fetch_images(url)

            if all_images:
                st.write_stream(stream_data(f"Đã kéo :blue-background[{len(all_images)}] ảnh từ URL"))
                # Download all images
                folder_name = download_images(all_images)
                zip_file = zip_images(folder_name)

                # Create a download button for the zipped images
                with open(zip_file, "rb") as f:
                    st.download_button(
                        label="Tải tất cả ảnh",
                        data=f,
                        file_name=zip_file,
                        mime="application/zip",
                    )
            else:
                st.write_stream(stream_data("No images found"))
        else:
            st.warning("Pass your URL to extract images")

    if all_images:
        display_images(all_images)
        for image in all_images:
            print(image)
        

if __name__ == "__main__":
    main()
