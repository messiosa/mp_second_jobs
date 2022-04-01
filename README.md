# Register of Members' (MPs) Financial Interests - structured

These scripts are designed to scrape data from various sources (including the MPFI register*) so journalists and the public can easily analyse the second job income of Members of Parliament.

The project uses spaCy named entity recognition (NER) models to pull data from the unstructured MPFI register.

For now, sheets are exported as .xlsx files with the date as the filename (e.g. 220228.xlsx). The MPFI register is updated every two weeks.

**Open up 220228.xlsx to see structured data from the MPFI register dated 28th February 2022. More dates coming soon.**

*https://publications.parliament.uk/pa/cm/cmregmem/contents2122.htm

## Files

For now, this project has not been uploaded to fork, so many of the necessary files are missing (e.g. the ner models and pkl files I've used). These are listed below.

**main.py** scrapers

**training.py** script for training new data for spacy models

**testing.py** where i test new functions

### from .gitignore -

**admin/** nothing interesting, notes etc

**excel/** excel files exported by scrapers

**old_files/** old versions of scrapers

**ner_models/** ner models (too big to upload here)

**pkl/** pkl files, mostly dicts which capture the data first time to avoid repeat scraping

**training_data/** text files used to train spaCy ner models

**testing.py** where i test new functions

**base_config.cfg / config.cfg / train.spacy** config files not included for now
