import tkinter as tk
import pandas as pd
import requests as r
from bs4 import BeautifulSoup
import re
from csv import reader
import os
import time
from datetime import datetime


def main(entry, radio_var):
    '''Entry point to the program, calls the functions and updates the labels to show progress'''

    input_path = entry
    radio_selection = radio_var.get()

    if not radio_selection: #if user doesn't select a coin, default to bitcoin
        radio_selection = "bitcoin"
    balances_path = balancesfile(input_path)
    addresses = openfile(input_path)
    querylist = loop(addresses, balances_path)

    dict = query(radio_selection, querylist, balances_path)
    #save the final csv will all balances
    final_df = pd.DataFrame.from_dict(dict, orient='index')
    label2.configure(text=f'Finished getting balances, results file has been saved here: \n {balances_path}')
    label2.update()
    final_df.to_csv(balances_path, mode='a')
    csv_write(balances_path)
    

def csv_write(balances_path):
    csv = pd.read_csv(balances_path)
    csv.columns = ['Addresses', 'Balance']
    csv['Balance'] = csv['Balance'].str.replace(r'BTC', '').astype(float)
    csv.loc['Total']= csv.sum(numeric_only=True, axis=0)
    csv.to_csv(balances_path, index=False)

def query(radio_selection, querylist, balances_path):
    '''
    Query blockchain.com with the btc address and scrape the balance. If a list is provided, will loop over the list until all addresses queried (even if query limited)
    Input: a btc address or list of btc addresses
    Return: A dictionary containing the btc address and its current balance
    '''
    querylist = set(querylist) #convert to a set to remove any duplicates

    if radio_selection == 'bitcoin':
        requesturl = 'https://www.blockchain.com/btc/address/'
    elif radio_selection == 'bitcoin_cash':
        requesturl = 'https://www.blockchain.com/bch/address/'
    elif radio_selection == 'ethereum':
        requesturl = 'https://www.blockchain.com/eth/address/'
    # elif radio_selection == 'litecoin':
    #     requesturl = #TODO: add litecoin

    try:
        dict = {}
        
        label.configure(text=f'Started: Querying {str(len(querylist))} addresses')
        label.update()
        for address in querylist:
            if address.startswith('bc1') or address.startswith('1') or address.startswith('3') or address.startswith('q') or address.startswith('0x'): #only read in valid BTC addresses #TODO: has to change for different coins
                requestlink = requesturl + address
                response = r.get(requestlink, timeout=25)
                content = response.content
                soup = BeautifulSoup(content, 'html.parser')
                balanceline = soup.find_all(class_=("sc-1ryi78w-0 cILyoi sc-16b9dsl-1 ZwupP u3ufsr-0 eQTRKC"))[2]
                balance = balanceline.find_all(text=re.compile("BTC"))
                dict[address] = balance
                # time.sleep(1) #15 definately works
                label2.configure(text=f'Querying address: \n{address}')
                label2.update()
            else:
                continue
        return dict
    except:
        time.sleep(20)
        label2.configure(text='Blockchain.com blocking requests: waiting 20 seconds to continue')
        label2.update()
        while not querylist: #list is empty
            querylist = loop(querylist, balances_path)
            label.configure(text=f'{str(len(querylist))} addresses left to query')
            label.update()
            query(querylist, balances_path)
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
            with open(files, 'r') as read_obj:
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

button = tk.Button(root, text = 'Get balance', command=lambda: main(entry.get(), radio_var))
button.grid(row=1, column=3, pady=5)

select_coin_label = tk.Label(root, text="Select a coin", font='Helvetica 12 bold')
select_coin_label.grid(row=2, column=3)

bitcoin_radio_button = tk.Radiobutton(root, text="Bitcoin", value="bitcoin", variable = radio_var)
bitcoin_radio_button.grid(row=3,column=3)
bitcoin_cash_radio_button = tk.Radiobutton(root, text="Bitcoin Cash", value="bitcoin_cash", variable = radio_var)
bitcoin_cash_radio_button.grid(row=4, column=3)
ethereum_radio_button = tk.Radiobutton(root, text="Ethreum", value="ethereum", variable = radio_var)
ethereum_radio_button.grid(row=5, column=3)

label = tk.Label(root)
label.grid(row=2, column=0)
label2 = tk.Label(root)
label2.grid(row=2,column=0)

root.mainloop()