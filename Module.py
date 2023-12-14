import requests
from bs4 import BeautifulSoup
import re

class Module:
    """
    Class to represent a module.
    """
    def __init__(self, url):
        self._url = url
        self._url_trimmed = self.url.split("/")[-1]
        self._title = None
        self._description = None
        self._dates = None
        self._rooms = None
        self._lecturers = None
        self._evaluation_metrics = None
        self._general_info = None

        self.get_landing_page_information()
    
    def get_landing_page_information(self):
        # Send a GET request to the given url
        response = requests.get(self._url)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            # Parse the HTML content of the response using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Use only the content of div tx-ciuniversity-course
            soup = soup.find('div', class_='tx-ciuniversity-course')
            
            sections = {"_general_info": "Allgemeine Information",
                         "_description": "Beschreibung",
                         "_prerequisites": "Voraussetzungen",
                         "_literature": "Literatur",
                         "_grading": "Leistungserfassung"}
            
            # Iterate over the sections and parse the content
            for key, header in sections.items():
                self.parse_subtopic(soup, key, header)

            # Parse the website URL
            self.parse_website_url(soup)

            # Parse lecturer information
            self.parse_lecturers(soup)

            # Parse title
            self._title = soup.find('h1').text.strip()

        else:
            print(f"Failed to retrieve the webpage {self._url}. Status code:", response.status_code)


    def parse_subtopic(self, soup, key, topic):
            # Find the h2 tag with text "Beschreibung" or "Description"
            # 't and' included to prevent error when t is None
            topic_h2 = soup.find('h2', string=topic)

            # If the h2 tag was found
            if topic_h2:

                content = ""

                # Iterate over the elements between the two h2 tags
                for element in topic_h2.next_siblings:
                    # if the element is of type h2, stop reading
                    if element.name == "h2":
                        break
                    # if the element is of type p, add the text to the description
                    if element.name == 'p' and element.text != "Zurück":
                        content += '\n' + element.text.strip()
                    # if the element is of type ul, add the text to the description
                    elif element.name == 'ul':
                        content += '\n' + self.parse_list(element)

                    # TODO check how this works with an example page like "https://hpi.de/studium/im-studium/lehrveranstaltungen/digital-health-ma/lehrveranstaltung/wise-23-24-3860-applied-probabilistic-machine-learning.html"
                    elif element.name == "li":
                        continue

                # Save the description
                self.__dict__[key] = content.strip()

    def parse_website_url(self, soup):
        # Find the text "Website zum Kurs"
        # re.compile is a workaround to find text embedded in Whitespaces
        website_text = soup.find(string=re.compile("Website zum Kurs"))

        # Initialize the variable to store the website URL
        website_url = None

        if website_text:
            # Iterate through the siblings to find the <a> tag
            for element in website_text.next_elements:
                # Check if the sibling is an <a> tag
                if element.name == "a":
                    website_url = element.get('href')
                    break
                # Stop looking before another h2 tag is reached
                if element.name == "h2":
                    break
        
        # Add the alternative website URL to the class dictionary
        self._website_url = website_url

    def parse_lecturers(self, soup):
        # Find the text "Dozent"
        # re.compile is a workaround to find text embedded in Whitespaces
        lecturer_heading = soup.find(string=re.compile("Dozent"))

        # Initialize the list to store the lecturers
        lecturers = None

        if lecturer_heading:
            lecturers = []
            # Iterate through the siblings to find the <i> tag
            for element in lecturer_heading.next_elements:
                # Check if the sibling is an <a> tag
                if element.name == "a":
                    lecturer_name = self.replace_whitespace(element.text)
                    # Stop searching as soon as the website URL is reached (next section)
                    if "https" in lecturer_name:
                        break
                    lecturers.append(lecturer_name)
                # Stop looking before another h2 tag is reached
                if element.name == "h2":
                    break
        
        # Write the lecturers to the class dictionary
        self._lecturers = lecturers
    
    def parse_list(self, ul):
        """
        Parses the content of the list items into a class dictionary.
        """
        list_items = ul.find_all('li')
        list_content = []

        for item in list_items:
            list_content.append("- " + self.replace_whitespace(item.text))

        return "\n".join(list_content)

    def replace_whitespace(self, string):
        """
        Replaces all whitespace characters with a single space.
        """
        ws_replaced = " ".join(string.split())
        return ws_replaced.strip()
        
    @property
    def url(self):
        return self._url
    
    @property
    def description(self):
        return self._description
    
    @property
    def dates(self):
        return self._dates
    
    @property
    def rooms(self):
        return self._rooms
    
    @property
    def lecturers(self):
        return self._lecturers
    
    @property
    def evaluation_metrics(self):
        return self._evaluation_metrics
