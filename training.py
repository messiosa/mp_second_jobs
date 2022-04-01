import spacy, pandas as pd
import random, tqdm, pickle, sys, random
from spacy.tokens import DocBin
from spacy.util import filter_spans

# 1. FOR TRAINING THE ALL_ENTS MODEL USE CREATE_ALL_ENTS_TXT_RANDOM/GIVENMP()
#       * YOU CAN USE _RANDOM TO CHOOSE RANDOM MPS TO TRAIN WITH, OR USE _GIVENMP TO TRAIN ON A SPECIFIC MP or _GIVENLIN to TRAIN ON A SPECIFIC LINE OF TEXT
#       * FILENAME = .TXT FILE WHERE TRAINING DATA IS STORED (IN ./TRAINING_DATA/)
#       * DATA = FEEDING CUSTOM DATA. LEAVE SET TO '0'.
#       * PARLUK_URL = PARLUK URL OF MP YOU WANT TO TRAIN MODEL WITH
#
# 1. FOR TRAINING THE TIME/MONEY MODELS USE CREATE_MONEYTIME_TXT()
#       * LIST_OF_MONEY_OR_TIME IS A LIST OF MONEY VALUES OR TIME VALUES TO TRAIN THE MODEL WITH
#
# 2. CREATE TRAIN.SPACY FILE WITH CREATE_TRAIN_DOT_SPACY_FILE
#
# 3. OPEN CMD LINE AND EXECUTE THE FOLLOWING LINES -
#       * cd C:\Users\messiosa\Documents\work\data_projects\mps_data
#       * python -m spacy train config.cfg --output ./ner_models/MODEL_NAME --paths.train ./train.spacy --paths.dev ./train.spacy


df = pd.DataFrame(pickle.load(open('./pkl/dict_df.pkl','rb')))

## CREATE TRAINING DATA - MAIN TRAINING DATA
def create_all_ents_txt_random(filename, data='0'):
    dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl','rb'))
    input_exit = ''

    ## CHECK LINE HASN'T ALREADY BEEN TRAINED
    with open(filename, 'r', encoding='utf-8') as f:
        training_data = f.readlines()
    trained_lines = []
    for line in training_data:
        trained_lines.append(list(eval(line))[0][0])

    def get_training_data(text, filename):
        ents_list = []
        org_ents = []
        money_ents = []
        time_ents = []
        date_ents = []
        role_ents = []

        print(text)
        try:
            input_org = input('Enter organizations:').split('#')
            input_money = input('Enter money:').split('#')
            input_time = input('Enter hours:').split('#')
            input_date = input('Enter dates:').split('#')
            input_role = input('Enter roles:').split('#')

            for x in input_org:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    org_ents.append((a,b,"ORG"))      
                else:
                    pass

            for x in input_money:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    money_ents.append((a,b,"MONEY"))
                else:
                    pass
    
            for x in input_time:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    time_ents.append((a,b,"TIME"))
                else:
                    pass
            
            for x in input_date:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    date_ents.append((a,b,"DATE"))
                else:
                    pass
                
            for x in input_role:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    role_ents.append((a,b,"ROLE"))
                else:
                    pass

        except:
            pass
        
        ents_list = org_ents+money_ents+time_ents+date_ents+role_ents
        print(ents_list,'\n')

        TRAIN_DATA = open(filename, 'a', encoding='utf-8')
        TRAIN_DATA.write(str((text, {'entities': ents_list}))+',\n')
        TRAIN_DATA.close()

    ## MAIN LOOP
    while input_exit != 'y':
        i = random.randrange(0,650)
        try:
            if data == '0':
                for text in list(dict_mpfi.values())[i]['1. Employment and earnings']:
                    if text['full_text'] in trained_lines:
                        pass
                    else:
                        get_training_data(text['full_text'], filename)
                        trained_lines.append(text['full_text'])
            elif data != '0':
                for line in data:
                    get_training_data(line[0], filename)
        except:
            pass
        input_exit = input('Exit? ') ## OPTION TO EXIT LOOP AFTER EVERY ENTRY

#create_all_ents_txt_random('./training_data/all_ents_data.txt', '0')

def create_all_ents_text_givenmp(parluk_url, filename):
    dict_mpfi = pickle.load(open('./pkl/dict_mpfi.pkl','rb'))
    dict_mplink_name = pickle.load(open('./pkl/dict_mplink_name.pkl','rb'))
    mp_dict_mpfi = dict_mpfi[dict_mplink_name[parluk_url]]

    input_exit = ''

    ## CHECK LINE HASN'T ALREADY BEEN TRAINED
    with open(filename, 'r', encoding='utf-8') as f:
        training_data = f.readlines()
    trained_lines = []
    for line in training_data:
        trained_lines.append(list(eval(line))[0][0])

    def get_training_data(text, filename):
        ents_list = []
        org_ents = []
        money_ents = []
        time_ents = []
        date_ents = []
        role_ents = []

        print(text)
        try:
            input_org = input('Enter organizations:').split('#')
            input_money = input('Enter money:').split('#')
            input_time = input('Enter hours:').split('#')
            input_date = input('Enter dates:').split('#')
            input_role = input('Enter roles:').split('#')

            for x in input_org:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    org_ents.append((a,b,"ORG"))      
                else:
                    pass

            for x in input_money:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    money_ents.append((a,b,"MONEY"))
                else:
                    pass
    
            for x in input_time:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    time_ents.append((a,b,"TIME"))
                else:
                    pass
            
            for x in input_date:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    date_ents.append((a,b,"DATE"))
                else:
                    pass
                
            for x in input_role:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    role_ents.append((a,b,"ROLE"))
                else:
                    pass

        except:
            pass
        
        ents_list = org_ents+money_ents+time_ents+date_ents+role_ents
        print(ents_list,'\n')

        TRAIN_DATA = open(filename, 'a', encoding='utf-8')
        TRAIN_DATA.write(str((text, {'entities': ents_list}))+',\n')
        TRAIN_DATA.close()

    ## MAIN LOOP
    while input_exit != 'y':
        try:
            for text in mp_dict_mpfi['1. Employment and earnings']:
                if text['full_text'] in trained_lines:
                    pass
                else:
                    get_training_data(text['full_text'], filename)
                    trained_lines.append(text['full_text'])
        except:
            pass
        input_exit = input('Exit? ') ## OPTION TO EXIT LOOP AFTER EVERY ENTRY

#create_all_ents_text_givenmp('buckland_robert.htm', './training_data/all_ents_data.txt')

def create_all_ents_text_givenline(line, filename):

    def get_training_data(text, filename):
        ents_list = []
        org_ents = []
        money_ents = []
        time_ents = []
        date_ents = []
        role_ents = []

        print(text)
        try:
            input_org = input('Enter organizations:').split('#')
            input_money = input('Enter money:').split('#')
            input_time = input('Enter hours:').split('#')
            input_date = input('Enter dates:').split('#')
            input_role = input('Enter roles:').split('#')

            for x in input_org:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    org_ents.append((a,b,"ORG"))      
                else:
                    pass

            for x in input_money:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    money_ents.append((a,b,"MONEY"))
                else:
                    pass
    
            for x in input_time:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    time_ents.append((a,b,"TIME"))
                else:
                    pass
            
            for x in input_date:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    date_ents.append((a,b,"DATE"))
                else:
                    pass
                
            for x in input_role:
                if x != 0:
                    a = text.find(x)
                    b = a + len(x) - 1
                    role_ents.append((a,b,"ROLE"))
                else:
                    pass

        except:
            pass
        
        ents_list = org_ents+money_ents+time_ents+date_ents+role_ents
        print(ents_list,'\n')

        TRAIN_DATA = open(filename, 'a', encoding='utf-8')
        TRAIN_DATA.write(str((text, {'entities': ents_list}))+',\n')
        TRAIN_DATA.close()

    ## MAIN LOOP
    get_training_data(line, filename)

#line = 'line of data'
#create_all_ents_text_givenline(line, './training_data/all_ents_data.txt')

## CREATE TRAINING DATA - MONEY DATA
def create_moneytime_txt(filename, list_of_money_or_time):
    input_exit =''

    TRAIN_DATA = open(filename, 'a', encoding='utf-8')

    while input_exit != 'y':
        i = random.randrange(0, len(list_of_money_or_time))
        item_text = list_of_money_or_time[i]
        print('\n'+item_text)
        item_ent = input('Enter period (1/D/W/2W/M/Q/Y): ')

        line = str((item_text, {'entities':[(0, len(item_text), item_ent)]}))+','
        TRAIN_DATA.write(line+'\n')

        input_exit = input('Exit? ') ## OPTION TO EXIT LOOP AFTER EVERY ENTRY
    
    TRAIN_DATA.close()

#new_list = ['list','of','data']
#create_moneytime_txt('./training_data/time_data.txt', new_list)

## TRAIN.SPACY FILE
def create_train_dot_spacy_file(training_data_txtfile):
    nlp = spacy.load('en_core_web_trf')
    db = DocBin()

    ## turn training data textfile into lines
    with open(training_data_txtfile, 'r', encoding='utf-8') as f:
        NEW_TRAIN_DATA = f.readlines()

    train_data = []
    for line in NEW_TRAIN_DATA:
        train_data.append(eval(line)[0])

    ## main function
    for text, annot in train_data:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span is None:
                print(start,end,label,"Skipping entity")
            else:
                ents.append(span)
        filtered = filter_spans(ents)
        doc.ents = filtered
        db.add(doc)

    db.to_disk("./train.spacy")

#create_train_dot_spacy_file('./training_data/period_data.txt')