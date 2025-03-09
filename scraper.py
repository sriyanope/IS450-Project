from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

def get_certificate_type(soup):
  a = soup.find("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  if a != None:
    a = a.find("h2")
    a = a.get_text().lower()
  if a != None:
    if "specialization" in a:
      type = "Specialization"
    elif "professional" in a:
      type = "Professional Certificate"
    elif "course" in a:
      type = "Course"
    return type
  return ""

def get_course_details(soup):
  course_details = ""
  a = soup.find_all("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  if len(a) > 1:
    a = a[1]
    b = a.find_all("h3")
    c = soup.find_all("div", class_= "css-yam6t")
    if a.find("div", class_="css-3odziz") != None:
      d = a.find_all("div", class_="css-3odziz")
      for i in range(len(c)):
        course_details += f"{b[i].get_text()}"
        course_details += f"\n{d[i].get_text()}"
        course_details += f"\n{c[i].find_all("h4")[0].get_text()}"
        for p in c[i].find_all("p"):
          course_details += f"\n • {" ".join(p.get_text().split())}"
        e = [a.get_text() for a in c[i].find_all("h4")]
        if len(e) > 1:
          course_details += f"\n{e[1]}\n"
        course_details += ", ".join([a.get_text() for a in soup.find_all("div", class_="css-yam6t")[i].find_all("span", class_="css-o5tswl")])
        course_details += "\n\n"
      course_details.rstrip().rstrip().rstrip()
    else:
      d = a.find_all("div", class_="css-chglhw")
      for i in range(len(c)):
        course_details += f"{b[i].get_text()}"
        course_details += f"\n{d[i].get_text()}"
        e = c[i].find("p", class_="css-4s48ix")
        if e != None:
          course_details += f"\n{e.get_text()}"
        course_details += f"\n{c[i].find_all("h4")[0].get_text()}"
        f = c[i].find_all("h5")
        g = c[i].find_all("ul")
        for j in range(len(f)):
          course_details += f"\n{f[j].get_text()}"
          for li in g[j].find_all("li"):
            course_details += f"\n • {li.get_text()}"
        course_details += "\n\n"
  return course_details

def get_course_description(soup):
  a = soup.find("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  course_description = getattr(a.find("h2"), "get_text", lambda: None)() if a else None
  if a != None:
    for b in a.find_all("p"):
      course_description += f"\n{b.get_text()}"
  return course_description

def get_course_outcomes(soup):
  course_outcomes = ""
  a = soup.find("div", class_="cds-9 css-2l7onx cds-11 cds-grid-item cds-56 cds-78")
  if a != None:
    course_outcomes += a.find("h2", class_="cds-119 cds-Typography-base css-bbd009 cds-121").get_text()
    for a in soup.find("div", class_="cds-9 css-2l7onx cds-11 cds-grid-item cds-56 cds-78").find_all("li"):
      course_outcomes += f"\n • {a.get_text()}"
  return course_outcomes

def get_details_to_know(soup):
  text1 = getattr(soup.find("div", class_="css-1qfxccv"), "get_text", lambda: None)()
  parent_div = soup.find("div", class_="cds-9 css-9271ok cds-11 cds-grid-item cds-56 cds-64 cds-76")
  text2 = None
  if parent_div:
    text2 = getattr(parent_div.find("p", class_="css-vac8rf"), "get_text", lambda: None)()
  details_to_know = ": ".join(filter(None, [text1, text2])) or ""
  a = soup.find_all("div", class_="cds-9 css-9271ok cds-11 cds-grid-item cds-56 cds-64 cds-76")
  for i in range(1, len(a)):
    b = a[i].find("div", class_="css-drc7pp")
    c = a[i].find("div", class_="css-vac8rf")
    d = a[i].find('div', class_='css-onm9p2')
    if b != None and c != None:
      details_to_know += f"\n{b.get_text()}: {c.get_text()}"
    elif d != None:
      details_to_know += f"\n{d.get_text()}"
  return details_to_know

def coursera_scraper(soup, url):
  course_data = {
    'course_title': getattr(soup.find("div", class_="css-1q5srzp"), "get_text", lambda: None)(),
    'org': getattr(soup.find("div", class_="css-kimdhf"), "get_text", lambda: None)(),
    'cert_type': get_certificate_type(soup),
    'enrolled': ((div := soup.find("div", class_="css-1qi3xup")) and (strong := div.find("strong")) and (span := strong.find("span")) and span.get_text()) or None,
    'series_type': getattr(soup.find("a", class_="cds-119 cds-113 cds-115 css-17cxvu3 cds-142"), "get_text", lambda: None)(),
    'rating': getattr(soup.find("div", class_="cds-119 cds-Typography-base css-h1jogs cds-121"), "get_text", lambda: None)(),
    'num_reviews': ((match := re.search(r'\d+', getattr(soup.find("p", class_="css-vac8rf"), "get_text", lambda: "")())) and match.group()) or None,
    'difficulty': (divs[2].find("div", class_="css-fk6qfz").get_text().replace(" level", "") if (divs := soup.find_all("div", class_="css-dwgey1")) and len(divs) > 2 and divs[2].find("div", class_="css-fk6qfz") else None),
    'url': url,
    'duration': (" ".join(getattr(divs[3], "stripped_strings", [])) if (divs := soup.find_all("div", class_="css-dwgey1")) and len(divs) > 3 else None),
    'what_youll_learn': "\n".join([a.get_text() for a in soup.find_all("li", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-64")]),
    'skills_youll_gain': "\n".join([skill.get_text() for skill in soup.find_all("a", class_="cds-119 cds-113 cds-115 css-113xph7 cds-142")]),
    'details_to_know': get_details_to_know(soup),
    'course_outcomes': get_course_outcomes(soup),
    'course_description': get_course_description(soup),
    'course_details': get_course_details(soup)
    }
  return course_data

def scrape_coursera(csv):
  count = 0
  url_df = pd.read_csv(csv)
  urls = url_df["course_url"].tolist()
  n = len(urls)
  columns = [
    "course_title", "org", "cert_type", "enrolled", "series_type", "rating", "num_reviews", 
    "difficulty", "url", "duration", "what_youll_learn", "skills_youll_gain", 
    "details_to_know", "course_outcomes", "course_description", "course_details"
    ]
  scraped_df = pd.DataFrame(columns=columns)
  for url in urls:
    print(f"Scraping {count+1}/{n} urls: {urls[count]}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    course_data = coursera_scraper(soup, url)
    course_data_df = pd.DataFrame([course_data])
    scraped_df = pd.concat([scraped_df, course_data_df], ignore_index=True)
    count += 1
  
  scraped_df.to_csv("test_scraped_data.csv", index=True)
  print("Scraping complete")

scrape_coursera("test_courses.csv")