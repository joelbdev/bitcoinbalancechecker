import tkinter as tk
import pandas as pd
import requests as r
from bs4 import BeautifulSoup
import re
from csv import reader
import os
import time
from datetime import datetime
import random


def main(entry, radio_var, headers_list):
    '''Entry point to the program, calls the functions and updates the labels to show progress'''

    if entry.endswith('/'):
        input_path = entry
    else:
        input_path = entry + '/'
    radio_selection = radio_var.get()

    if not radio_selection: #if user doesn't select a coin, default to bitcoin
        radio_selection = "BTC"
    balances_path = balancesfile(input_path)
    addresses = openfile(input_path)
    querylist = loop(addresses, balances_path) 

    dict = query(radio_selection, querylist, balances_path, headers_list)
    #save the final csv will all balances
    
    csv_write(balances_path, dict, radio_selection)
    

def csv_write(balances_path, dict, radio_selection):
    """
    Write the final csv file with all the balances and total the balances
    Input: Path to allbalances file, dict containing addresses and balances and what coin balance the program is querying
    Return: nil
    """
    final_df = pd.DataFrame.from_dict(dict, orient='index')
    final_df.columns = ['Balance']
    label2.configure(text=f'Finished getting balances, results file has been saved here: \n {balances_path}')
    label2.update()

    final_df['Balance'] = final_df['Balance'].str.replace(radio_selection, '').astype(float) 
    final_df.loc['Total']= final_df.sum(numeric_only=True, axis=0)
    final_df.to_csv(balances_path, mode='a')

def query(radio_selection, querylist, balances_path, headers_list):
    '''
    Query blockchain.com with the btc address and scrape the balance. If a list is provided, will loop over the list until all addresses queried (even if query limited)
    Input: a btc address or list of btc addresses
    Return: A dictionary containing the btc address and its current balance
    '''
    querylist = set(querylist) #convert to a set to remove any duplicates
    if radio_selection == 'BTC':
        requesturl = 'https://www.blockchain.com/btc/address/'
        ticker = 'BTC'
    elif radio_selection == 'BCH':
        requesturl = 'https://www.blockchain.com/bch/address/'
        ticker = 'BCH'
    elif radio_selection == 'ETH':
        requesturl = 'https://www.blockchain.com/eth/address/'
        ticker = 'ETH'
    # elif radio_selection == 'litecoin':    print(final_df.head())

    #     requesturl = #TODO: add litecoin



    try:
        dict = {}
        label.configure(text=f'Started: Querying {str(len(querylist))} addresses')
        label.update()
        for address in querylist:
            time.sleep(1)
            if address.startswith('bc1') or address.startswith('1') or address.startswith('3') or address.startswith('q') or address.startswith('0x'): #only read in valid BTC addresses #TODO: has to change for different coins
                requestlink = requesturl + address
                headers = random.choice(headers_list)
                r.headers = headers
                response = r.get(requestlink, timeout=25)
                content = response.content
                soup = BeautifulSoup(content, 'html.parser')
                balanceline = soup.find_all(class_= ("sc-1ryi78w-0 cILyoi sc-16b9dsl-1 ZwupP u3ufsr-0 eQTRKC"))[5]
                balance = balanceline.find_all(text=re.compile(ticker)) 
                dict[address] = balance
                # time.sleep(1) #15 definately works
                label2.configure(text=f'Querying address: \n{address}')
                label2.update()
        
            else:
                #skip anything that isn't a cryptocurrency address e.g. CSV headers
                continue
        
    except r.exceptions.RequestException as e:
        time.sleep(20)
        label2.configure(text='Blockchain.com blocking requests: waiting 20 seconds to continue')
        print(e)
        label2.update()
        while not querylist: #Keep going until list is empty
            querylist = loop(querylist, balances_path)
            label.configure(text=f'{str(len(querylist))} addresses left to query')
            label.update()
            query(radio_selection, querylist, balances_path, headers_list)
    return dict

def loop(addresses, balances_path):
    '''
    Read in a csv file containing btc addresses and balances for the purposes of avoiding duplicate queries.
    Input: the csv file containing output of the query function
    Return: a list of btc addresses that have not yet had their balance queried
    '''
    alreadyqueried = []
    with open(balances_path, 'r') as all_bal:
        for row in all_bal:
            alreadyqueried.append(row[1])
    
    querylist = [elem for elem in addresses if elem not in alreadyqueried]
    return querylist

def openfile(input_path):
    '''
    Open a csv file with bitcoin addresses and write these addresses to a list
    Input: csv file containing bitcoin addresses in the first column
    Return: a list of bitcoin addresses
    '''

    addresses = []
    for files in os.listdir(input_path):
        if files.endswith('.csv') and not files.startswith('allbalances'):
            with open(f'{input_path}{files}', 'r') as read_obj:
                csv_reader = reader(read_obj)
                for row in csv_reader:
                    addresses.append(row) #ignore the header

    #flatten list of lists obtained from reading the files
    flattened = [val for sublist in addresses for val in sublist]
    return flattened

def balancesfile(input_path):
    '''
    Creates a balancefile to hold the queried balances
    Input: the path to create the balances file
    Return: an empty balances csv file
    '''
    date = datetime.now()
    allbalancesfile = f'allbalances {date}.csv'
    with open(f'{input_path}{allbalancesfile}', 'w') as newfile:
        pass 
    balances_path = input_path + allbalancesfile
    return balances_path

#Entry point is the GUI

headers_list = [
    # Firefox 77 Mac
     {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Chrome 83 Mac
    {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    # Chrome 83 Windows 
    {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
]


root = tk.Tk()
root.title('Balance checker')
radio_var = tk.StringVar()

root.geometry("500x220+300+300")
root.columnconfigure(1, weight=1)
root.columnconfigure(3, pad=7)
root.rowconfigure(3, weight=1)
root.rowconfigure(5, pad=7)

label1 = tk.Label(root, text='Enter directory containing csv files', font='Helvetica 14 bold')
label1.grid(sticky=tk.W)

entry = tk.Entry(root, width=45)
entry.grid(row=1, column=0, sticky=tk.N+tk.S, pady=5)

button = tk.Button(root, text = 'Get balance', command=lambda: main(entry.get(), radio_var, headers_list))
button.grid(row=1, column=3, pady=5)

select_coin_label = tk.Label(root, text="Select a coin", font='Helvetica 12 bold')
select_coin_label.grid(row=2, column=3)

bitcoin_radio_button = tk.Radiobutton(root, text="Bitcoin", value="BTC", variable = radio_var)
bitcoin_radio_button.grid(row=3,column=3)
bitcoin_cash_radio_button = tk.Radiobutton(root, text="Bitcoin Cash", value="BCH", variable = radio_var)
bitcoin_cash_radio_button.grid(row=4, column=3)
ethereum_radio_button = tk.Radiobutton(root, text="Ethreum", value="ETH", variable = radio_var)
ethereum_radio_button.grid(row=5, column=3)

label = tk.Label(root)
label.grid(row=2, column=0)
label2 = tk.Label(root)
label2.grid(row=2,column=0)

root.mainloop()
