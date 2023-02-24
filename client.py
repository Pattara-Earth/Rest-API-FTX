import time
import hmac
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, List
from requests import Request, Session, Response

class FtxClient:
    
    _ENDPOINT = 'https://ftx.com/api'
    
    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name
        self._session = Session()
    
    def _sign_request(self, request: Request) -> None:
        ts = int(time.time()*1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, res: Response) -> Any:
        try:
            data = res.json()
        except ValueError:
            res.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
        return data['result']
        
    def _request(self, method: str, path: str, **kwargs: Optional[Dict[str, Any]]) -> Any:
        # method: 'GET', kwargs: params
        # method: 'POST', kwargs: json 
        # method: 'DELETE', kwargs: json
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        res = self._session.send(request.prepare())
        return self._process_response(res)

# ---------------- Subaccount ----------------  

    def get_all_subaccount(self) -> List[dict]:
        return self._request('GET', '/subaccounts')

    def change_subaccount_name(self, sub: str, newSub: str) -> Dict:
        return self._request('POST', '/subaccounts/update_name', json={
            "nickname": sub,
            "newNickname": newSub,
        })
    
    def transfer_subaccount(self, coin: str, size: float, source: str, destination: str) -> Dict:
        return self._request('POST', '/subaccounts/transfer', json={
            "coin": coin,
            "size": size,
            "source": source,
            "destination": destination,
        })
# ---------------- Market ----------------
    def get_market(self, market_name: str) -> dict:
        return self._request('GET', f'/markets/{market_name}')
        
    def get_orderbook(self, market_name: str, depth: int = 20) -> Dict:
        # depth default 20, max 100
        return self._request('GET', f'/markets/{market_name}/orderbook', params={'depth': depth})
            
    def get_history_price(
        self, market_name: str, resol: int = 300, 
        start: float = None, end: float = None
    ) -> List[Dict]:
        # 'timeframes': {
        #         '15s': '15',
        #         '1m': '60',
        #         '5m': '300',
        #         '15m': '900',
        #         '1h': '3600',
        #         '4h': '14400',
        #         '1d': '86400',
        #         '3d': '259200',
        #         '1w': '604800',
        #         '2w': '1209600',
        #         # the exchange does not align candles to the start of the month
        #         # it can only fetch candles in fixed intervals of multiples of whole days
        #         # that works for all timeframes, except the monthly timeframe
        #         # because months have varying numbers of days
        #         '1M': '2592000',
        #     },
        return self._request('GET', f'/markets/{market_name}/candles', params={
                'resolution': resol,
                'start_time': start,
                'end_time': end,
        })
                                
# ---------------- Future ----------------    
    def get_future(self, future_name: str) -> dict:
        return self._request('GET', f'/futures/{future_name}')
    
    def get_funding_rates(self) -> List[dict]:
        return self._request('GET', '/funding_rates')
       
# ---------------- Account ----------------  
    def get_account(self) -> dict:
        return self._request('GET', '/account')
    
    def get_snapshot_historical_balances(self, accounts: List[str], endtime: float) -> dict:
        return self._request('POST', '/historical_balances/requests', json={
            "accounts": accounts,
            "endTime": endtime,
        })
    
    def get_historical_balances(self, request_id: int) -> dict:
        return self._request('GET', f'/historical_balances/requests/{request_id}') 
    
    def get_all_historical_balances(self) -> List[dict]:
        return self._request('GET', '/historical_balances/requests')

    def get_position(self) -> List[dict]:
        return self._request('GET', '/positions')
    
    def set_leverage(self, lev: int) -> dict:
        return self._request('POST', '/account/leverage', json={'leverage':lev})
    
# ---------------- Wallet ----------------  

    def get_coin_details(self) -> List[dict]:
        return self._request('GET', '/wallet/coins')   

    def get_balances(self) -> List[dict]:
        return self._request('GET', '/wallet/balances')
    
    def get_deposit_address(self, coin: str, method: str = None) -> dict:
        # For ERC20 tokens: method=erc20
        # For TRC20 tokens: method=trx
        # For SPL tokens: method=sol
        # For Omni tokens: method=omni
        # For BEP2 tokens: method=bep2
        # For Binance Smart Chain tokens: method=bsc
        # For Fantom tokens: method=ftm
        # For Avax tokens: method=avax
        # For Matic tokens: method=matic
        return self._request('GET', f'/wallet/deposit_address/{coin}', params={'method':method})
    
    def req_withdrawal(
        self, coin: str, size: float, address: str, tag: str = None, method: str = None, 
        withdraw_password: str = None, twoFA: str = None
    ) -> dict: 
        return self._request('POST', '/wallet/withdrawals', json={
            "coin": coin,
            "size": size,
            "address": address,
            "tag": tag,
            "method": method,
            "password": withdraw_password,
            "code": twoFA,
        })

# ---------------- Order Management ----------------  
    def get_order_history(
        self, market: str, side: str = None, orderType: str = None, 
        start: float = None, end: float = None
    ) -> List[dict]:
        return self._request('GET', f'/orders/history?market={market}', params={
            'side': side,
            'orderType': orderType,
            'start_time': start,
            'end_time': end
        })

    def get_pending_order(self, market: str) -> List[dict]:
        return self._request('GET', '/orders', params={'market':market})
    
    def place_order(
        self, market: str, side: str, price: float, types: str, size: float, 
        reduceOnly: bool = False, ioc: bool = False, postOnly: bool = False, 
        cliendId: str = None
    ) -> dict:
        # types 'limit' or 'market'
        return self._request('POST', '/orders', json={
            "market": market,
            "side": side,
            "price": price,
            "type": types,
            "size": size,
            "reduceOnly": reduceOnly,
            "ioc": ioc,
            "postOnly": postOnly,
            "clientId": cliendId
        })
    
    def modify_order(self, order_id: str, size: float, price: float) -> dict:
        return self._request('POST', f'/orders/{order_id}/modify', json={
            "size": size,
            "price": price,
        })
    
    def get_order_status(self, order_id: str) -> dict:
        return self._request('GET', f'/orders/{order_id}')
    
    def cancel_order(self, order_id: str) -> dict:
        return self._request('DELETE', '/orders', json={'order_id': order_id})
    
    def cancel_all_orders(self, market: str) -> dict:
        return self._request('DELETE', '/orders', json={'market': market})
    
# ---------------- Fill ---------------- 
    def get_fills(
        self, market: str, starttime: float = None, 
        endtime: float = None, order_id: float = None
    ) -> List[dict]:
        return self._request('GET', f'/fills?market={market}', params={
            'start_time': starttime,
            'end_time': endtime,
            'orderId': order_id,
        })

    def get_funding_payments(self) -> dict:
        return self._request('GET', '/funding_payments')


if __name__ == "__main__":

    pass