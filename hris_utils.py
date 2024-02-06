#hris_utils.py
#%%
import datetime
import logging
import sys
import pandas as pd

def get_logger(log_file, log_level=logging.INFO):
    logger = logging.getLogger('applogger')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


def parse_selection_input(selection:str) -> list[int]:
    '''Selection string composed of digits, commas, dashes
        (e.g., '1,5-7,12')'''
    result = []
    for part in selection.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return result


def get_user_input(companyCSV):
    df_companies = pd.read_csv(companyCSV)
    company_names = df_companies.company_name.to_list()
    company_query = "\n".join([f'{i} - {name}' for i,name in enumerate(company_names)])
    approved_set = '0123456789,-'
    while True:
        compID = input("Companies:\n" + company_query + "\nEnter Company #s (0 for all, X to Exit): ")
        if compID in 'Xx': return None,None
        if all([c in approved_set for c in compID]): break
        print(f'Try again: Approved characters: {approved_set}')
    compIDs = list(range(1,len(company_names))) if compID == '0' else parse_selection_input(compID)    
    return df_companies, compIDs


def START_DATE(YEARS_BACK = 2):
    '''YTD plus this many years'''
    d = datetime.date.today()
    return datetime.datetime(year=d.year-YEARS_BACK, month=1, day=1)
# %%
