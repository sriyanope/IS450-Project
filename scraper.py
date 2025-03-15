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
    return type
  return None

def get_course_details_from_program(soup):
  program_details = ""
  a = soup.find_all("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  if len(a) > 1:
    a = a[1]
    course_titles = a.find_all("h3")
    sections = soup.find_all("div", class_= "css-yam6t")
    if a.find("div", class_="css-3odziz") != None:
      for i in range(len(sections)):
        program_details += course_titles[i].get_text().strip() + "|"
        lo_description = ""
        for p in sections[i].find_all("p"):
          paragraph = " ".join(p.get_text().split())
          if paragraph.strip() != "":
            lo_description += paragraph + ";"
        program_details += lo_description[:-1] + "|"
        
        course_skills = ";".join([a.get_text() for a in soup.find_all("div", class_="css-yam6t")[i].find_all("span", class_="css-o5tswl")])
        program_details += course_skills + "||"
    else:
       print("DIDNT HAVE ELSE STATEMENT FOR COURSE DETAILS") # delete if not flagged out after testing
  return program_details[:-2]

def get_module_details(soup, url):
  mod_dict = {"url": [],
              "mod_title": [],
              "mod_description": [],
              "videos": []
              }
  
  a = soup.find_all("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  if len(a) > 1:
    a = a[1]
    mod_titles = a.find_all("h3")
    sections = soup.find_all("div", class_= "css-yam6t")
    for i in range(len(sections)):
      mod_dict["url"].append(url)
      mod_dict["mod_title"].append(mod_titles[i].get_text().strip())
      
      p = sections[i].find("p")
      paragraph = " ".join(p.get_text().split()).strip()
      mod_dict["mod_description"].append(paragraph)
      
      g = sections[i].find_all("ul")
      videos = ""
      if (sections[i].find_all("h5")[0].get_text().split("•")[0].split(" ")[1] == "videos"):
        for video in g[0].find_all("li"):
          videos += video.get_text().split("•")[0] + ";"
        videos = videos[:-1]
      mod_dict["videos"].append(videos)

  return mod_dict

def get_description(soup):
  a = soup.find("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
  if a == None:
     return None
  return ";".join([b.get_text() for b in a.find_all("p")])

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

def program_scraper(soup, url):
  program_data = {
    'prog_title': getattr(soup.find("div", class_="css-1q5srzp"), "get_text", lambda: None)(),
    'org': getattr(soup.find("div", class_="css-kimdhf"), "get_text", lambda: None)(),
    'cert_type': get_certificate_type(soup),
    'enrolled': ((div := soup.find("div", class_="css-1qi3xup")) and (strong := div.find("strong")) and (span := strong.find("span")) and span.get_text()) or None,
    'num_courses': getattr(soup.find("a", class_="cds-119 cds-113 cds-115 css-17cxvu3 cds-142"), "get_text", lambda: None)()[0],
    'rating': getattr(soup.find("div", class_="cds-119 cds-Typography-base css-h1jogs cds-121"), "get_text", lambda: None)(),
    'num_reviews': ((match := re.search(r'\d+', getattr(soup.find("p", class_="css-vac8rf"), "get_text", lambda: "")())) and match.group()) or None,
    'difficulty': (divs[2].find("div", class_="css-fk6qfz").get_text().replace(" level", "") if (divs := soup.find_all("div", class_="css-dwgey1")) and len(divs) > 2 and divs[2].find("div", class_="css-fk6qfz") else None),
    'prog_lo_description': ";".join([a.get_text().strip() for a in soup.find_all("li", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-64")]),
    'prog_lo_skills': ";".join([skill.get_text().strip() for skill in soup.find_all("a", class_="cds-119 cds-113 cds-115 css-113xph7 cds-142")]),
    'prog_description': get_description(soup),
    'course_title_description_skills': get_course_details_from_program(soup),
    'url': url,
    }
  return program_data

def course_scraper(soup, url, program_id):
  course_data = {
    'program_id': program_id,
    'course_title': getattr(soup.find("div", class_="css-1q5srzp"), "get_text", lambda: None)(),
    'num_modules': getattr(soup.find("a", class_="cds-119 cds-113 cds-115 css-17cxvu3 cds-142"), "get_text", lambda: None)()[0],
    'lo_description': ";".join([a.get_text().strip() for a in soup.find_all("li", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-64")]),
    'lo_skills': ";".join([skill.get_text().strip() for skill in soup.find_all("a", class_="cds-119 cds-113 cds-115 css-113xph7 cds-142")]),
    'course_description': get_description(soup),
    'url': url,
    }
  return course_data

def main(csv, include_children=True):
  count = 1
  url_df = pd.read_csv(csv)
  urls = url_df["url"].tolist()
  n = len(urls)
  
  parent_columns = [
    "prog_title", "org", "cert_type", "enrolled", "num_courses", "rating", "num_reviews", 
    "difficulty", "prog_lo_description", "prog_lo_skills", "prog_description", 
    "course_title_description_skills", "url"
    ]
  
  course_columns = ["program_id", "course_title", "num_modules", "lo_description", "lo_skills", "course_description", "url"]

  module_columns = ["url", "mod_title", "mod_description", "videos"]
  
  parent_df = pd.DataFrame(columns=parent_columns)
  course_df = pd.DataFrame(columns=course_columns)
  module_df = pd.DataFrame(columns=module_columns)
  all_child_urls = []
  
  # First pass: scrape parent URLs and collect child URLs
  for url in urls:
    print(f"Scraping program {count}/{n} url: {urls[count-1]}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Scrape the parent page
        course_data = program_scraper(soup, url)
        course_data_df = pd.DataFrame([course_data])
        parent_df = pd.concat([parent_df, course_data_df], ignore_index=True)
        
        # Extract child URLs if this option is enabled
        if include_children:
            child_urls = extract_child_urls(soup, url)
            all_child_urls.append(child_urls)
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    
    count += 1

    # Continually save results
    if count % 20 == 0:
      parent_df.to_csv("prog_scraped.csv", index=True)
  parent_df.to_csv("prog_scraped.csv", index=True)

  # Second pass: scrape all child URLs
  if include_children and all_child_urls:
    total_children = len(all_child_urls)
    
    for i in range(len(all_child_urls)):
      child_urls = all_child_urls[i]
      print(f"Scraping course set {i+1}/{total_children}")
        
      for url in child_urls:
        try:
          response = requests.get(url)
          soup = BeautifulSoup(response.content, "html.parser")
          
          # Scrape the child page, marking it as a child with its parent URL
          course_data = course_scraper(soup, url, i)
          course_data_df = pd.DataFrame([course_data])
          course_df = pd.concat([course_df, course_data_df], ignore_index=True)

          module_data = get_module_details(soup, url)
          module_data_df = pd.DataFrame(module_data)
          module_df = pd.concat([module_df, module_data_df], ignore_index=True)
                
        except Exception as e:
            print(f"Error scraping child URL {url}: {e}")
        
        # Save the results
        if i % 20 == 0:
          course_df.to_csv("course_scraped.csv", index=False)
          module_df.to_csv("module_scraped.csv", index=False)
    course_df.to_csv("course_scraped.csv", index=False)
    module_df.to_csv("module_scraped.csv", index=False)
  print("Scraping complete")
  print(f"Summary: Scraped {len(parent_df)} parent courses and {len(course_df)} child courses")
  return

main("test_courses.csv", include_children=True)