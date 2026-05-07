API_KEY = 'eQRE2IoS3ozOzYHgDzLF4P3nOkIEVoMZtkVjlzRWURnbqKEpkbTYoSXP5silKN6a'
SECRET = 'lFXZunP4Od3MXr7BdSIo1l8cbjdOKvmnNpw38zuEH0Sa8plR12EOEqdlN7EJjCaX'
BASE_URL = 'https://testnet.binance.vision/key/api/v3/order'
from datetime import datetime
import requests
import hashlib
import hmac
import time
quantity = 20
params = {
    
    'symbol': 'ADAUSDT',
    'side': 'BUY',
    'type':'MARKET',
    'quantity': quantity,
    'timestamp': int(time.time()*1000)
}
query_string = '&'.join([f'{key}={params[key]}'for key in params])
signature = hmac.new(SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
params['signature'] = signature
response = requests.post(BASE_URL, params=params, headers={'X-MBX-APIKEY': API_KEY})

print(response.json())