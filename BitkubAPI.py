import json
import hmac
import hashlib
import requests
import numpy as np
import pandas as pd
from datetime import datetime


class BitkubAPI():
    
    def __init__(self, API_HOST, API_KEY, API_SECRET, symbol=None):
        self.API_HOST = API_HOST
        self.API_KEY = API_KEY
        self.API_SECRET = bytes(API_SECRET, encoding='utf-8')
        self.header = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-BTK-APIKEY': API_KEY,
        }
        self.symbol = symbol
        
    def json_encode(self, data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)

    def sign(self, data):
        j = self.json_encode(data)
        #print('Signing payload: ' + j)
        h = hmac.new(self.API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
        return h.hexdigest()

    def timeserver(self):
        response = requests.get(self.API_HOST + '/api/servertime')
        ts = int(response.text)
        return ts
        
    def allSymbol(self):
        response = requests.get(self.API_HOST + '/api/market/symbols')
        symbols = pd.DataFrame(response.json()['result'])
        return symbols
        
    def getPrice(self):
        pair = self.symbol
        response = requests.get(self.API_HOST + '/api/market/ticker')
        price = float(response.json()[pair]['last'])
        return price
    
    def createBuy(self, amount, rate, typ):
        data = {
            'sym': self.symbol, # THB_XLM
            'amt': amount, # THB amount you want to spend 
            'rat': rate, # Price
            'typ': typ, # limit Order
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/place-bid', headers=self.header, data=self.json_encode(data))
        r = r.json()
        
        if r['error'] == 0:
            print(f'Buy {typ}: {self.symbol} @{rate:.2f} amount: {amount:.2f} THB')
            
        elif r['error'] == 18:
            print(f'Error 18: Insufficient balance.')
        
        elif r['error'] == 15:
            print('Error 15: Amount too low.')
        
        else:
            print('Error: Please check the code.')

    
    def createSell(self, amount, rate, typ):
        data = {
            'sym': self.symbol, # THB_XLM
            'amt': amount, # XLM unit you want to sell 
            'rat': rate, # Price
            'typ': typ, # limit Order
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/place-ask', headers=self.header, data=self.json_encode(data))
        r = r.json()
        
        if r['error'] == 0:
            print(f'Sell {typ}: {self.symbol} @{rate:.2f} amount: {amount:.2f} unit')
            
        elif r['error'] == 18:
            print(f'Error 18: Insufficient balance.')
        
        elif r['error'] == 15:
            print('Error 15: Amount too low.')
        
        else:
            print('Error: Please check the code.')
        
        
    def my_open_orders(self):
        data = {
            'sym': self.symbol,
            'ts' : self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/my-open-orders', headers=self.header, data=self.json_encode(data))
        r = r.json()['result']
        df_r =  pd.DataFrame(r, columns=['id', 'side', 'type', 'rate', 'fee', 'amount', 'receive'])
        return df_r 
        
    def cancelOrder(self, order_id, side):
        data = {
            'sym': self.symbol,
            'id': order_id,
            'sd': side,
            'ts' : self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/cancel-order', headers=self.header, data=self.json_encode(data))
        r = r.json()
        
        if r['error'] == 21:
            print(f'Order ID: {order_id} Invalid order for cancellation.')
            
        elif r['error'] == 0:
            print(f'Order ID: {order_id} has been cancelled.')
        
        else:
            print('Cancel error please check the code.')
            
            
    def wallet(self): # Get user available balances
        data = {
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/wallet', headers=self.header, data=self.json_encode(data))
        r = r.json()['result']
        return r
    
    def balances(self): 
        # Includes both available and reserved balances
        # coin = 'THB', 'XLM'
        data = {
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/balances', headers=self.header, data=self.json_encode(data))
        r = r.json()['result']
        df_total = pd.DataFrame.from_dict(r) # .sum(axis=0)
        return df_total
    
    def order_history(self):
        data = {
            'sym': self.symbol,
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/my-order-history', headers=self.header, data=self.json_encode(data))
        r = r.json()['result']
        df_r = pd.DataFrame(r)
        return df_r
    
    def cancelAllOrder(self):
        order_id = self.my_open_orders()['id']
        side = self.my_open_orders()['side']
        for i,j in zip(order_id,side):
            self.cancelOrder(i, j)
    
    def order_info(self, order_id, side):
        # For check status
        data = {
            'sym': self.symbol,
            'id': order_id,
            'sd': side,
            'ts': self.timeserver(),
        }
        
        signature = self.sign(data)
        data['sig'] = signature
        r = requests.post(self.API_HOST + '/api/market/order-info', headers=self.header, data=self.json_encode(data))
        r = r.json()['result']
        df_r = pd.DataFrame(r)
        return df_r
    
    def getPriceHistory(self, tf, frm=None, to=None):
        params = {
            'sym': self.symbol,
            'int': tf, # 60 900 3600 86400
            'frm': frm,
            'to': to,
        }
        
        signature = self.sign(params)
        params['sig'] = signature
        
        #'sym=THB_XLM&lmt=1'
        r = requests.get(self.API_HOST + '/api/market/tradingview', params=self.json_encode(params))
        r = r.json()['result']
        df_r = pd.DataFrame(r)
        return df_r
        
# fetch price history


if __name__ == "__main__":

    bk = BitkubAPI(API_HOST='https://api.bitkub.com',
                API_KEY='', 
                API_SECRET='',
                symbol='')

    

