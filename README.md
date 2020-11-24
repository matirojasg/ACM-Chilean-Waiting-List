# The Chilean Waiting List Corpus.

Code for the paper Advances in Automatic Detection of Medical and Dental Entities in Clinical Referrals in Spanish.

## Install

Run `pip install -r requirements.txt` to install all dependencies and download statistic Spanish pre-trained
model `python -m spacy download es_core_news_lg`.

## Convert brat files into conll files.

Run the script in `main.py`. The results will be saved in `resources/conll_format`. 

## Data analysis.

Run the script in `data_analysis.py`. The results will be will be printed to console and the json files will be saved in `resources/json_files`. 


