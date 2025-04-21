# Furniture Product Name Extractor

## Project Overview

This project focuses on extracting product names from furniture store websites. It utilizes a custom Named Entity Recognition (NER) model, built with **spaCy**, integrated into a **Django** web application. The goal is to provide a simple interface for users to input a website URL and receive a list of identified furniture product names from that page.

## How It Works

The application receives a URL from the user via a web form. The Django backend then:
1.  Uses **Requests** and **BeautifulSoup4** to scrape the webpage content and extract the primary text.
2.  Processes this text with the custom-trained **spaCy NER model** (loaded on startup) to identify and list entities labeled as `PRODUCT`.
3.  Displays the results back to the user on the webpage.
The application is deployed on **Render** using **Gunicorn** and **WhiteNoise**.

## Technology Stack

*   **Backend:** Python, Django
*   **NLP / NER:** spaCy
*   **Web Scraping:** Requests, BeautifulSoup4
*   **Web Server/Deployment:** Gunicorn, WhiteNoise, Render
*   **Frontend:** HTML, CSS

## Key Features

*   Web-based interface for URL submission.
*   Extraction of product names using a custom NER model.
*   Display of extracted product name list.
*   Basic handling of inaccessible URLs or pages without clear text.

## Model Development

The underlying NER model was developed through a process involving:
1.  **Scraping** text data from target furniture websites.
2.  **Manually annotating** product names within the collected text (using tools like Label Studio).
3.  **Training** a spaCy NER model on this custom-annotated dataset.

## Live Demo

You can try out the application by visiting the following link:

**[https://furniture-product-extractor.onrender.com]**
*(https://furniture-product-extractor.onrender.com)*

## Future Work / Potential Improvements

*   Implement asynchronous processing for scraping to handle slow websites without blocking the user interface.
*   Enhance the scraper's robustness to handle JavaScript-rendered content.
*   Expand the training dataset for the NER model to improve accuracy and coverage across more diverse site structures.
*   Add features to display extracted prices or other relevant product details alongside the names.
*   Improve UI/UX feedback during processing.

## Conclusion

This project successfully demonstrates a practical approach to extracting specific information (product names) from diverse web sources using a combination of web scraping and a custom spaCy NER model within a Django framework. While developed as a Proof of Concept, the core components are scalable and adaptable for further development or different extraction tasks.
