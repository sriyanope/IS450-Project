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
      course_description += f";{b.get_text()}"
  return course_description

def extract_child_urls(soup, parent_url):
    """Extract child course URLs from a parent page (specialization or certificate program)"""
    child_urls = []
    
    sdp_links = soup.find_all("a", attrs={"data-click-key": lambda v: v and "sdp_course_list_link" in v})
    for link in sdp_links:
        if link.has_attr("href") and "/learn/" in link["href"]:
            href = link["href"]
            base_href = href.split("?")[0]
            full_url = "https://www.coursera.org" + base_href if base_href.startswith("/") else base_href
            child_urls.append(full_url)
    
    # Remove duplicates and filter out the parent URL
    child_urls = list(set(child_urls))
    if parent_url in child_urls:
        child_urls.remove(parent_url)

    return child_urls

def parent_scraper(soup, url):
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
    'lo_description': ";".join([a.get_text() for a in soup.find_all("li", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-64")]),
    'lo_skills': ";".join([skill.get_text() for skill in soup.find_all("a", class_="cds-119 cds-113 cds-115 css-113xph7 cds-142")]),
    'course_description': get_course_description(soup),
    'course_details': get_course_details(soup)
    }
  
  # If we couldn't find the title using the original selector, try other common selectors
  if not course_data['course_title']:
      h1_element = soup.find("h1", class_=lambda c: c and "css-" in c)
      if h1_element:
          course_data['course_title'] = h1_element.get_text()
  
  # Extract ratings from span if not found in the original way
  if not course_data['rating']:
      rating_span = soup.find("span", class_=lambda c: c and "css-15ld0c5" in c)
      if rating_span:
          course_data['rating'] = rating_span.get_text().strip()
  
  # Extract skills from tags with class css-o5tswl
  if not course_data['lo_skills']:
      skills = soup.find_all("span", class_="css-o5tswl")
      if skills:
          course_data['lo_skills'] = ", ".join([skill.get_text() for skill in skills])
      
  return course_data

def child_scraper(soup, url, parent_id):
  course_data = {
    'parent_id': parent_id,
    'course_title': getattr(soup.find("div", class_="css-1q5srzp"), "get_text", lambda: None)(),
    'org': getattr(soup.find("div", class_="css-kimdhf"), "get_text", lambda: None)(),
    'cert_type': get_certificate_type(soup),
    'enrolled': ((div := soup.find("div", class_="css-1qi3xup")) and (strong := div.find("strong")) and (span := strong.find("span")) and span.get_text()) or None,
    'series_type': getattr(soup.find("a", class_="cds-119 cds-113 cds-115 css-17cxvu3 cds-142"), "get_text", lambda: None)(),
    'rating': getattr(soup.find("div", class_="cds-119 cds-Typography-base css-h1jogs cds-121"), "get_text", lambda: None)(),
    'num_reviews': ((match := re.search(r'\d+', getattr(soup.find("p", class_="css-vac8rf"), "get_text", lambda: "")())) and match.group()) or None,
    'difficulty': (divs[2].find("div", class_="css-fk6qfz").get_text().replace(" level", "") if (divs := soup.find_all("div", class_="css-dwgey1")) and len(divs) > 2 and divs[2].find("div", class_="css-fk6qfz") else None),
    'url': url,
    'lo_description': ";".join([a.get_text() for a in soup.find_all("li", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-64")]),
    'lo_skills': ";".join([skill.get_text() for skill in soup.find_all("a", class_="cds-119 cds-113 cds-115 css-113xph7 cds-142")]),
    'course_description': get_course_description(soup),
    'course_details': get_course_details(soup)
    }
  
  # If we couldn't find the title using the original selector, try other common selectors
  if not course_data['course_title']:
      h1_element = soup.find("h1", class_=lambda c: c and "css-" in c)
      if h1_element:
          course_data['course_title'] = h1_element.get_text()
  
  # Extract ratings from span if not found in the original way
  if not course_data['rating']:
      rating_span = soup.find("span", class_=lambda c: c and "css-15ld0c5" in c)
      if rating_span:
          course_data['rating'] = rating_span.get_text().strip()
  
  # Extract skills from tags with class css-o5tswl
  if not course_data['lo_skills']:
      skills = soup.find_all("span", class_="css-o5tswl")
      if skills:
          course_data['lo_skills'] = ", ".join([skill.get_text() for skill in skills])
      
  return course_data

def main(csv, include_children=True):
  count = 1
  url_df = pd.read_csv(csv)
  urls = url_df["url"].tolist()
  n = len(urls)
  
  parent_columns = [
    "course_title", "org", "cert_type", "enrolled", "series_type", "rating", "num_reviews", 
    "difficulty", "url", "lo_description", "lo_skills", "course_description", "course_details"
    ]
  
  child_columns = [
    "parent_id", "course_title", "org", "cert_type", "enrolled", "series_type", "rating", "num_reviews", 
    "difficulty", "url", "lo_description", "lo_skills", "course_description", "course_details"
  ]
  
  parent_df = pd.DataFrame(columns=parent_columns)
  child_df = pd.DataFrame(columns=child_columns)
  all_child_urls = []
  
  # First pass: scrape parent URLs and collect child URLs
  for url in urls:
    print(f"Scraping parent {count}/{n} urls: {urls[count-1]}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Scrape the parent page
        course_data = parent_scraper(soup, url)
        course_data_df = pd.DataFrame([course_data])
        parent_df = pd.concat([parent_df, course_data_df], ignore_index=True)
        
        # Extract child URLs if this option is enabled
        if include_children:
            child_urls = extract_child_urls(soup, url)
            all_child_urls.append(child_urls)
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    
    count += 1

    # Save results
    parent_df.to_csv("parents.csv", index=True)
  
  # Second pass: scrape all child URLs
  if include_children and all_child_urls:
    child_count = 0
    total_children = len(all_child_urls)
    
    for i in range(len(all_child_urls)):
        child_urls = all_child_urls[i]

        print(f"Scraping child set {i+1}/{total_children}")
        
        for url in child_urls:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Scrape the child page, marking it as a child with its parent URL
                course_data = child_scraper(soup, url, i)
                course_data_df = pd.DataFrame([course_data])
                child_df = pd.concat([child_df, course_data_df], ignore_index=True)
                
            except Exception as e:
                print(f"Error scraping child URL {url}: {e}")
  
  # Save the results
  child_df.to_csv("children.csv", index=False)
  print("Scraping complete")
  
  print(f"Summary: Scraped {len(parent_df)} parent courses and {len(child_df)} child courses")
  
  return

main("test_courses.csv")