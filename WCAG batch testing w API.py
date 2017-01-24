# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
import numpy as np


# Register at http://wave.webaim.org/api/
wave_api_key = '7q58g54k597' 

# INPUT: Flat file with one URL per line, looks in current folder
input_filename = 'test short.txt'

# OUTPUT: replaces existing file with that name, otherwise creates it
output_filename = 'test short.xlsx'

# True: show on-screen process indicators; False: Don't show.
on_screen_process = True


def call_wave_api(page_URL):
    
    wave_api_URL = "http://wave.webaim.org/api/request"
    
    params = {"key": wave_api_key, 
              "url": page_URL,
              "format": "json",
              "reporttype": 1
              }


    # ERROR HANDLING 1: REQUESTS
    try:
        # requests.get returns JSON string
        r = requests.get(wave_api_URL, params=params, timeout=21)
    except requests.exceptions.Timeout:
        return_string = 'Operation timed out without response.'
        return return_string
    except requests.exceptions.TooManyRedirects:
        return_string = 'Bad URL, too many redirects.'
        return return_string
    except requests.exceptions.RequestException as e:
        return e
    

    # ERROR HANDLING 2: API 
    if r.status_code == requests.codes.ok:
        # API call returns wrong encoding, need to hard-code
        r.encoding = 'utf-8'
        # convert json string to json dictionary
        return r.json()
    else:
        return r.status_code, r.raise_for_status()
        
        
        
def convert_wcag_errors_to_score(wcag_errors):
    
    if wcag_errors < 10:
        return 3
    elif wcag_errors >= 10 and wcag_errors < 20:
        return 2
    elif wcag_errors >= 20 and wcag_errors < 30:
        return 1
    else:
        return 0
    
    

def main():

    # READ LIST OF USER-SUBMITTED URLs
    # encoding parameter important for cases where URLs have non-ASCII characters
    file_URLs = open(input_filename, mode='r', encoding='utf_8')
    
    # CREATE LIST STRUCTURE FOR STORING ALL URLS TO TEST
    list_URLs = []
    
    for line in file_URLs:         
        list_URLs.append(line.strip()) # use .strip() to remove leading and trailing whitespace and end of line characters
        
    file_URLs.close()
            
    
    # TODO: LOCATE URL TO A RANDOM SUB-PAGE FOR EACH USER-SUBMITTED URL, ADD TO list_URLs
    #
    #

    
    # VARIABLE USED IN ON-SCREEN PROCESS INDICATOR
    total_URLs = len(list_URLs)
    
    
    # CREATE DATAFRAME TO STORE API TEST RESULTS
    df_result = pd.DataFrame(columns=['Web page title', 'Web page URL', 'Number of WCAG errors', 'Detailed WCAG report'])
    
    # CREATE DATAFRAME TO STORE API TEST PROBLEMS
    df_problems = pd.DataFrame(columns=['Web page URL', 'Problem details'])
    number_problems = 0
    
    # CALL API TO TEST EACH URL, ADD RESULT TO DATAFRAME
    for i, URL in enumerate(list_URLs):
        if on_screen_process: print('Testing URL ', i + 1, ' of ', total_URLs, '.')

        URL_result = call_wave_api(URL)   
 
        try:
            # process relevant data fields: pagetitle, page url and number of WCAG errors
            # the following two lines obsolete since UTF-8 encoding enforced API call result
            #pagetitle_unicode = bytes(URL_result['statistics']['pagetitle'],'iso-8859-1').decode('utf-8')
            #df_result.loc[i] = [pagetitle_unicode, URL_result["statistics"]["pageurl"], URL_result["statistics"]["waveurl"], URL_result["categories"]["error"]["count"]]        
            df_result.loc[i] = [URL_result['statistics']['pagetitle'], URL_result["statistics"]["pageurl"], URL_result["categories"]["error"]["count"], URL_result["statistics"]["waveurl"]]        
            
            if on_screen_process: print('OK', ': ', URL)
        
        except:
            # handle errors in API call return
            None
            df_problems.loc[i] = [URL, URL_result]            
            number_problems += 1
            
            if on_screen_process: print('ERROR', ': ', URL)
            if on_screen_process: print(URL_result)

              
        if on_screen_process: print('\n')
            
 
    # CREATE EXCEL FILE OBJECT FOR EXPORT
    excel_writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
         
    
    # DATAFRAME 1: RESULTS
    
    # Reset dataframe index to create continuous row numbers starting with 1
    df_result = df_result.reset_index(drop=True)
    df_result.index += 1
    
    # ON-SCREEN PROCESS INDICATOR
    if on_screen_process: print('Writing results to Excel file.')
    
    # EXPORT RESULTS TO EXCEL
    df_result.to_excel(excel_writer, sheet_name='List of URLs')
    
    
    # DATAFRAME 2: SYNTHESIS
    
    # SYNTHESISE THE DATASET
    avg_wcag_errors = np.mean(df_result['Number of WCAG errors'])
    mean_wcag_errors = np.median(df_result['Number of WCAG errors'])
    number_URLs_ok = len(df_result)
    score = convert_wcag_errors_to_score(avg_wcag_errors)

    synthesis = {'Average number of WCAG errors'    : avg_wcag_errors,
                 'Median number of WCAG errors'     : mean_wcag_errors,
                 'URLs successfully tested'         : number_URLs_ok,
                 'Indicator score (points)'         : score,
                 'URL problems (see separate sheet)': number_problems
                 }
    
    # CONVERT SYNTHESIS DICT TO DATAFRAME
    # First one no longer works in py3.5             
    #df_synthesis = pd.DataFrame(synthesis.items(), columns=['Title', 'Value'])
    df_synthesis = pd.DataFrame.from_dict(synthesis, orient='index')
        
    # EXPORT SYNTHESIS TO EXCEL (SAME FILE, DIFFERENT SHEET)
    df_synthesis.to_excel(excel_writer, sheet_name='Synthesis')  
    
    
    # DATAFRAME 3: URL PROBLEMS
    
    # Reset dataframe index to create continuous row numbers starting with 1
    df_problems = df_problems.reset_index(drop=True)
    df_problems.index += 1
    
    # EXPORT LIST OF PROBLEMATIC URLS TO EXCEL (SAME FILE, DIFFERENT SHEET)
    df_problems.to_excel(excel_writer, sheet_name='URL problems')
    
    
    # FINALISE EXCEL EXPORT
    excel_writer.save()
    
    if on_screen_process: print('Done.')

if __name__ == '__main__':
    main()