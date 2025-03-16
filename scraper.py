from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd
import re

def get_certificate_type(soup):
    h2_text = soup.find("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94").find("h2").get_text().lower()
    
    cert_types = {
        "specialization": "Specialization",
        "professional": "Professional Certificate"
    }

    for keyword, cert_type in cert_types.items():
        if keyword in h2_text:
            return cert_type
    return None

def get_course_details_from_program(soup):
    program_details = []
    content_divs = soup.find_all("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
    
    if len(content_divs) <= 1:
        return ""
        
    content_div = content_divs[1]
    course_titles = content_div.find_all("h3")
    sections = soup.find_all("div", class_="css-yam6t")
    
    # Check if we have the right structure
    if not content_div.find("div", class_="css-3odziz"):
        return ""
    
    for _, (title, section) in enumerate(zip(course_titles, sections)):
        # Extract course title
        course_title = title.get_text().strip()
        
        # Extract descriptions
        descriptions = []
        for p in section.find_all("p"):
            text = " ".join(p.get_text().split()).strip()
            if text:
                descriptions.append(text)
        
        # Extract skills
        skills = [span.get_text() for span in section.find_all("span", class_="css-o5tswl")]
        
        # Build course details string
        course_detail = f"{course_title}|{';'.join(descriptions)}|{';'.join(skills)}"
        program_details.append(course_detail)
    
    return "||".join(program_details)

def get_description(soup):
    a = soup.find("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
    if a == None:
        return None
    return ";".join([b.get_text() for b in a.find_all("p")])

def extract_course_urls(soup, parent_url):
    """Extract course course URLs from a parent page (specialization or certificate program)"""
    course_urls = []
    
    sdp_links = soup.find_all("a", attrs={"data-click-key": lambda v: v and "sdp_course_list_link" in v})
    for link in sdp_links:
        if link.has_attr("href") and "/learn/" in link["href"]:
            href = link["href"]
            base_href = href.split("?")[0]
            full_url = "https://www.coursera.org" + base_href if base_href.startswith("/") else base_href
            course_urls.append(full_url)
    
    # Remove duplicates and filter out the parent URL
    course_urls = list(set(course_urls))
    if parent_url in course_urls:
        course_urls.remove(parent_url)
    return course_urls

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

def module_scraper(soup, url):
    mod_dict = {
        "url": [],
        "mod_title": [],
        "mod_description": [],
        "videos": []
    }
    
    content_divs = soup.find_all("div", class_="cds-9 css-0 cds-11 cds-grid-item cds-56 cds-79 cds-94")
    if len(content_divs) <= 1:
        return mod_dict
        
    content_div = content_divs[1]
    mod_titles = content_div.find_all("h3")
    sections = soup.find_all("div", class_="css-yam6t")
    
    for i, (title, section) in enumerate(zip(mod_titles, sections)):
        mod_dict["url"].append(url)
        mod_dict["mod_title"].append(title.get_text().strip())
        
        # Get module description
        p_tag = section.find("p")
        description = " ".join(p_tag.get_text().split()).strip() if p_tag else ""
        mod_dict["mod_description"].append(description)
        
        # Get video information
        video_list = []
        h5_tags = section.find_all("h5")
        
        if h5_tags and "videos" in h5_tags[0].get_text().split("•")[0].split():
            video_items = section.find_all("ul")[0].find_all("li") if section.find_all("ul") else []
            video_list = [item.get_text().split("•")[0].strip() for item in video_items]
        
        mod_dict["videos"].append(";".join(video_list))
    
    return mod_dict

def scrape_course_url(url, parent_id, session):
    try:
        response = session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        course_data = course_scraper(soup, url, parent_id)
        module_data = module_scraper(soup, url)
        
        return {"course_data": course_data, "module_data": module_data}
    except Exception as e:
        print(f"Error scraping course URL {url}: {e}")
        return None

def main(csv, include_course=True):
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
    all_course_urls = []
    
    # First pass: scrape program URLs and collect course URLs
    session = requests.Session()
    for url in urls:
        print(f"Scraping program {count}/{n}")
        try:
            response = session.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Scrape the parent page
            course_data = program_scraper(soup, url)
            course_data_df = pd.DataFrame([course_data])
            parent_df = pd.concat([parent_df, course_data_df], ignore_index=True)
            
            # Extract course URLs if this option is enabled
            if include_course:
                course_urls = extract_course_urls(soup, url)
                all_course_urls.append(course_urls)
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        count += 1

        # Continually save results
        if count % 20 == 0:
            parent_df.to_csv("prog_scraped.csv", index=True)
    parent_df.to_csv("prog_scraped.csv", index=True)

    # Second pass: scrape all course URLs
    if include_course and all_course_urls:
        flattened = [url for sublist in all_course_urls for url in sublist]
        course_urls = pd.DataFrame(flattened, columns=["url"])
        course_urls.to_csv("course_urls.csv", index=False)
        print("-----Child URLs Saved-----")

        total_course = len(all_course_urls)
        session = requests.Session()
        
        course_df = pd.DataFrame(columns=course_columns)
        module_df = pd.DataFrame(columns=module_columns)
        
        # Process in batches for better efficiency
        batch_size = 10
        
        for batch_start in range(0, total_course, batch_size):
            batch_end = min(batch_start + batch_size, total_course)
            print(f"Processing batch {batch_start//batch_size + 1}")
            
            batch_course_results = []
            batch_module_results = []
            
            # Process each parent's course URLs in the current batch
            for i in range(batch_start, batch_end):
                course_urls = all_course_urls[i]
                print(f"Scraping course set {i+1}/{total_course}")
                
                with ThreadPoolExecutor(max_workers=9) as executor:
                    futures = [executor.submit(scrape_course_url, url, i, session) for url in course_urls]
                    
                    for future in futures:
                        result = future.result()
                        if result:
                            # Append to batch results
                            course_data_df = pd.DataFrame([result["course_data"]])
                            batch_course_results.append(course_data_df)
                            
                            module_data_df = pd.DataFrame(result["module_data"])
                            batch_module_results.append(module_data_df)
            
            # Concatenate batch results and add to main DataFrames
            batch_course_df = pd.concat(batch_course_results, ignore_index=True)
            course_df = pd.concat([course_df, batch_course_df], ignore_index=True)
            
            batch_module_df = pd.concat(batch_module_results, ignore_index=True)
            module_df = pd.concat([module_df, batch_module_df], ignore_index=True)
            
            # Save intermediate results after each batch
            course_df.to_csv("course_scraped.csv", index=False)
            module_df.to_csv("module_scraped.csv", index=False)
            
            print(f"Saved progress: {len(course_df)} courses and {len(module_df)} module entries")

        print(f"Final results: {len(course_df)} courses and {len(module_df)} module entries")

main("programs.csv", include_course=True)