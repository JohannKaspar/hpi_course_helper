import random
import requests
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from collections import defaultdict
from helpers import courses_dict

class CourseModule:
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
        self.soup = None


    @retry(
        stop=stop_after_attempt(4), # Maximum number of retries
        wait=wait_exponential(multiplier=1, min=1, max=60) # Exponential backoff
    )
    def make_request(self):
        """
        Sends a GET request to the given url and returns the response.
        """
        return requests.get(self._url)
        

    def get_soup(self):
        """
        Creates the BeautifulSoup object of the module's landing page.
        """
        try:
            response = self.make_request()
            self.soup = BeautifulSoup(response.text, 'html.parser')
            # We need only the content of div tx-ciuniversity-course
            self.soup = self.soup.find('div', class_='tx-ciuniversity-course')
        except requests.exceptions.RequestException as e:
            print("FAILED:", e)
        

    def get_landing_page_information(self):
        if not self.soup:
            self.get_soup()

        # Parse general information
        self.get_general_info()

        # Parse the module groups
        self.get_module_groups()

        # Parse general description, prerequisites, literature, grading, dates
        self.get_subtopic_content()

        # Parse the website URL
        self.get_website_url()

        # Parse lecturer information
        self.get_lecturers()

        # Parse title
        # match everything before " (W" or " (S"
        self.get_title()

    
    def get_title(self):
        title = self.soup.find('h1').text.strip()
        match = re.match("\s*(.*[\S])\s+\(W|S", title)
        if match:
            self._title = match.group(1)
        else:
            self._title = title

    def get_evaluation_metrics(self):
        # create a soup from the stored HTML
        evaluation_metrics = json.load(open("course_evaluation.json", "r"))

        # get the evaluation metrics for the module
        evaluation_metrics = evaluation_metrics.get(self._title.lower())

        if evaluation_metrics:
            self._evap_grade: float = evaluation_metrics.get("grade")
            self._evap_semester: str = evaluation_metrics.get("semester")
        else:
            # assign a random float between 1.0 and 3.2
            self._evap_grade: float = round(random.uniform(1.0, 3.2), 1)
            self._evap_semester: str = "WiSe 2025/26"


    def get_subtopic_content(self):
        sections = {
            "_description": "Beschreibung",
            "_prerequisites": "Voraussetzungen",
            "_literature": "Literatur",
            "_grading": "Leistungserfassung",
            "_dates": "Termine"
            }
        
        # Iterate over the sections and parse the content
        for key, header in sections.items():
            # Find the h2 tag with text "Beschreibung" or "Description"
            # 't and' included to prevent error when t is None
            h2 = self.soup.find('h2', string=header)

            # If the h2 tag was found
            if h2:
                content = ""
                # Iterate over the elements between the two h2 tags
                for element in h2.next_siblings:
                    # if the element is of type h2, stop reading
                    if element.name == "h2":
                        break
                    # if the element is of type p, add the text to the description
                    if element.name == 'p' and element.text != "Zurück":
                        content += '\n' + element.text.strip()
                    # if the element is of type ul, add the text to the description
                    elif element.name == 'ul':
                        content += '\n' + self.parse_list_to_string(element)

                    # TODO check how this works with an example page like "https://hpi.de/studium/im-studium/lehrveranstaltungen/digital-health-ma/lehrveranstaltung/wise-23-24-3860-applied-probabilistic-machine-learning.html"
                    elif element.name == "li":
                        continue

                # Save the description
                self.__dict__[key] = content.strip()


    def get_general_info(self):
        h2 = self.soup.find('h2', string="Allgemeine Information")
        # If the h2 tag was found
        if h2:
            content = {}
            # Iterate over the elements between the two h2 tags
            for element in h2.next_siblings:
                if element.name == 'ul':
                    content.update(self.parse_list_to_dict(element))
                # if the element is of type h2, stop reading
                if element.name == "h2":
                    break
            # Save the description
            self.__dict__["_general_info"] = content

    
    def get_module_groups(self):
        course_module_groups = []
        for course_name in list(courses_dict.keys()):
            # this checks if the course name is on the page of the module
            course_name_element = self.soup.find("div", class_="tx_dscclipclap_header", string=re.compile(course_name))

            if course_name_element:
                # get the parent element of the module_course_element
                module_course_element = course_name_element.parent
                module_groups_text = self.replace_whitespace(module_course_element.text)
                # Match all module groups XXXX and subgroups YY which are of type "HPI-XXXX-YY" without the "HPI-" prefix
                matches = re.findall(r"HPI-([A-Z]{2,6})(?:-([A-Z]+))?", module_groups_text)
                if matches:
                    for module_group, subgroup in matches:
                        # In some cases the module group is incorrectly formatted as PSK123 instead of PSK-123
                        if module_group.startswith("PSK") and len(module_group) >= 6 and subgroup == "":
                                module_group, subgroup = module_group[:3], module_group[3:]
                        # Add the module group to the dictionary
                        course_module_groups.append((
                            courses_dict.get(course_name),
                            module_group,
                            subgroup))
        self._module_groups = course_module_groups        


    def get_website_url(self):
        # Find the text "Website zum Kurs"
        # re.compile is a workaround to find text embedded in Whitespaces
        website_text = self.soup.find(string=re.compile("Website zum Kurs"))

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

    def get_lecturers(self):
        # Find the text "Dozent"
        # re.compile is a workaround to find text embedded in Whitespaces
        lecturer_heading = self.soup.find(string=re.compile("Dozent"))

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
    
    def _list(self, ul):
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
        return re.sub(r"\s+", " ", string).strip()
       

    def parse_list_to_string(self, ul):
        """
        Parses the content of the list items into a string.
        """
        list_items = ul.find_all('li')
        list_content = []

        for item in list_items:
            list_content.append(self.replace_whitespace(item.text.strip()))
        return "- ".join(list_content)



    def parse_list_to_dict(self, ul):
        """
        Parses the content of the list items into a dictionary.
        """
        list_items = ul.find_all('li')
        list_content = {}

        for item in list_items:
            li_text = self.replace_whitespace(item.text)
            list_content[li_text.split(":")[0]] = li_text.split(":")[1].strip()
        return list_content


    @property
    def url(self):
        return self._url
    
    @property
    def url_trimmed(self):
        return self._url_trimmed
    
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
        return ", ".join(self._lecturers)
    
    @property
    def evap_grade(self):
        return self._evap_grade
    
    @property
    def evap_semester(self):
        return self._evap_semester
    
    @property
    def credits(self):
        return self._general_info.get("ECTS")
    
    @property
    def website(self):
        return self._website_url

    @property
    def title(self):
        return self._title
    

    @property
    def module_groups(self):
        return self._module_groups

