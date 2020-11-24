# The Chilean Waiting List Corpus.

Code for the paper Advances in Automatic Detection of Medical and Dental Entities in Clinical Referrals in Spanish.

## Install

Run `pip install -r requirements.txt` to install all dependencies and download statistic Spanish pre-trained
model `python -m spacy download es_core_news_lg`.

## Convert brat files into conll files.

Run the script in `main.py`. The results will be saved in `resources/conll_format`.

Example: python main.py --output_filename entities --multi_conll True --lower_tokens True --no_accent_marks 
True --verbose True --types Medication Disease Finding Procedure

You can decide to add some extra arguments as shown above. The meaning of each argument is as follows:

- output_filename: Conll file name (default = Entities)
- multi_conll: True if you want to keep both outer and inner entities in multi conll format. (default = False)
- lower_tokens: True if you want to leave lower tokens. (default = False)
- no_accent_marks: It replaces (á, é, í, ó, ú) characters by (a, e, i, o, u) (default = False)
- verbose: True if you want verbose prints in the console. (default = False)
- types: You can decide which entities to keep in conll file. (default = None)


## Data analysis.

Run the script in `data_analysis.py`. The results will be will be printed to console and the json files will be saved in `resources/json_files`. 