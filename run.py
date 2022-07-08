import os

dates = [
    ('220627','27 June 2022'),
    ('220530','30 May 2022'),
    ('220516','16 May 2022'),
    ('220503','3 May 2022'),
    ('220419','19 April 2022'),
    ('220328','28 March 2022'),
    ('220314','14 March 2022'),
    ('220228','28 February 2022'),
    ('220214','14 February 2022'),
    ('220131','31 January 2022'),
    ('220117','17 January 2022'),
    ('220104','4 January 2022')
]

for date, date_words in dates:
    os.system('python3 main.py '+'"'+date+'"'+' '+'"'+date_words+'"')