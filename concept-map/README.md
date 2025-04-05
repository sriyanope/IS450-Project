## generating network diagram based on given topics and concepts
- take the html file generated from berttopic - feed it in below scripts
- run `create_course_topics.py` and `create_module_terms.py` to generate a csv of topics/concepts gathered from topic modelling 
- prompt details are in `prompt.txt`, follow them with intended model
- run script `create-nodes-edge.py` to create the nodes and edges csv for gephi later on by running the following command 
  `python3 create-nodes-edge.py <path to json for LLM output`
- run `generate-viz.py` to generate the visualisations
