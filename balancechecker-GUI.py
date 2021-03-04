import tkinter as tk
import pandas as pd
import requests as r
from bs4 import BeautifulSoup
import re
from csv import reader
import os
import time
from datetime import datetime

def main(entry):
    '''Entry point to the program, calls the functions and updates the labels to show progress'''

    input_path = entry
    balances_path = balancesfile(input_path)
    addresses = openfile(input_path)
    querylist = loop(addresses, balances_path)

    dict = query(querylist, balances_path)
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
    csv.to_csv(balances_path)

def query(querylist, balances_path):
    '''
    Query blockchain.com with the btc address and scrape the balance. If a list is provided, will loop over the list until all addresses queried (even if query limited)
    Input: a btc address or list of btc addresses
    Return: A dictionary containing the btc address and its current balance
    '''
    querylist = set(querylist) #convert to a set to remove any duplicates
    try:
        dict = {}
        
        label.configure(text=f'Started: Querying {str(len(querylist))} addresses')
        label.update()
        for address in querylist:
            if address.startswith('bc1') or address.startswith('1') or address.startswith('3'): #only read in valid BTC addresses
                requesturl = f'https://www.blockchain.com/btc/address/{address}'
                response = r.get(requesturl, timeout=25)
                content = response.content
                soup = BeautifulSoup(content, 'html.parser')
                balanceline = soup.find_all(class_=("sc-1ryi78w-0 cILyoi sc-16b9dsl-1 ZwupP u3ufsr-0 eQTRKC"))[2]
                balance = balanceline.find_all(text=re.compile("BTC"))
                dict[address] = balance
                # time.sleep(1) #15 definately works
                label2.configure(text=f'Querying address: {address}')
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

HEIGHT = 800
WIDTH = 900


root = tk.Tk()
root.title('Balance checker')

canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
canvas.pack()

frame = tk.Frame(root, bd=5)
frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.1, anchor='n')

label1 = tk.Label(frame, text='Enter directory containing csv files')
label1.config(font=('helvetica,10'))
label1.pack()

entry = tk.Entry(frame, font=40)
entry.pack()

button = tk.Button(frame, text="Get Balances", font=40, command=lambda: main(entry.get()))
button.place(relx=0.7, relheight=1, relwidth=0.3)
button.pack()

lower_frame = tk.Frame(root, bd=10)
lower_frame.place(relx=0.5, rely=0.25, relwidth=0.75, relheight=0.6, anchor='n')

label = tk.Label(lower_frame)
label.pack()

label2 = tk.Label(lower_frame)
label2.pack()

root.mainloop()




