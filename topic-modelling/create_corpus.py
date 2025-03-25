import pandas as pd
import re

def preprocess_text(text):
    if isinstance(text, str):
        # Convert to lowercase
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        text = re.sub(r'[^a-z\s\'-]', '', text)
        stop_words = ["course", "program", "learn", "outcome", "outcomes", "work",
                    "description", "skill", "skills", "module", "modules", "specialization", "specialisation",
                    "summary", "certificate", "certificates", "professional", "career", "opportunity", "opportunities",
                    "experience", "experiences", "videos", "video", "readings", "assignment", "applied learning project",
                    "in this", "you will", "this week", "week", "youll", "assignments", "meet your instructor", "overview",
                    "we will", "well"]
        pattern = r'\b(?:' + '|'.join(stop_words) + r')\b'
        text = re.sub(pattern, '', text)
        return re.sub(r'\s+', ' ', text).strip()
    return ""

try:
    prog_df = pd.read_csv('data/prog_scraped.csv')
    course_df = pd.read_csv('data/course_scraped.csv')
    module_df = pd.read_csv('data/module_scraped.csv')
    prog_df.rename(columns={"Unnamed: 0": "id"}, inplace=True)
    grouped_module_df = module_df.groupby("url").agg(list)
    
    # Process each program
    for _, program in prog_df.iterrows():
        program_id = program['id']
        corpus_file = f"topic-modelling/corpus/program{program_id}.txt"
        
        try:
            with open(corpus_file, 'w', encoding='utf-8') as f:
                # Program information
                prog_title = preprocess_text(program['prog_title'])
                prog_desc = ""
                raw_desc =  program['prog_description'].split(";")
                for desc in raw_desc:
                    prog_desc += preprocess_text(desc) + "\n"
                f.write(f"<DOC>\n{prog_title}\n{prog_desc}</DOC>\n\n")
                
                # Get courses for this program
                program_courses = course_df[course_df['program_id'] == program_id]
                
                # Process each course
                for _, course in program_courses.iterrows():
                    course_url = course['url']
                    num_modules = int(course['num_modules'])
                    course_title = preprocess_text(course['course_title'])
                    course_desc = ""
                    raw_desc = course['course_description'].split(";")
                    for desc in raw_desc:
                        course_desc += preprocess_text(desc) + "\n"
                    f.write(f"<DOC>\n{course_title}\n{course_desc}")
                    
                    # Get modules for this course
                    course_modules = grouped_module_df.loc[course_url]
                    
                    # Process each module
                    title, desc, videos = course_modules
                    for i in range(num_modules):
                        mod_title = preprocess_text(title[i])
                        mod_desc = preprocess_text(desc[i])
                        vids = ""
                        if i < len(videos):
                            if type(videos[i]) == str:
                                vids = preprocess_text(" ".join(videos[i].split(";"))) + "\n"
                        f.write(f"\n{mod_title}\n{mod_desc}\n{vids}")
                    
                    f.write(f"</DOC>\n\n")
            
            print(f"Created corpus file for program {program_id}")
        
        except Exception as e:
            print(f"Error processing program {program_id}: {e}")
        
    print(f"Created corpus files for {len(prog_df)} programs")

except Exception as e:
    print(f"Error loading CSV files: {e}")
