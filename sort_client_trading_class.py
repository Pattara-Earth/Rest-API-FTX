from rest_api.client import FtxClient

class ClassicSpot(FtxClient):
    def __init__(self, api_key, api_secret, subaccount_name=None, symbol=None, postOnly=False):
        super().__init__(api_key, api_secret, subaccount_name)
        self.api_key = api_key
        self.api_secret = api_secret
        self.subaccount = subaccount_name
        self.symbol = symbol
        self.asset_name = self.symbol.split('/')[0]
        self.cash_name = self.symbol.split('/')[1]
        self.postOnly = postOnly
    
    def get_price(self):
        return float(self.get_market(self.symbol)['price'])
    
    def get_previous_price(self): 
        orders = self.get_fills(self.symbol)
        if not orders:
            return float(1000000)
        return float(orders[0]['price'])

    def create_order(self, side, price, types, size):
        try:
            return self.place_order(self.symbol, side, price, types, size, postOnly=self.postOnly)
        except Exception as err:
            return f'ERROR: {err}'
             
    def get_pending_order(self):
        return super().get_pending_order(self.symbol)
    
    def cancel_all_symbol_orders(self):
        orders = self.get_pending_order()
        if not orders: 
            return 'No orders for cancel'
        else:
            for order in orders:
                self.cancel_order(float(order['id']))
            return 'Orders queued for cancellation'

    def get_pair_coins(self):
        balances = self.get_balances()
        coins = [self.asset_name, self.cash_name]
        return {
            items['coin']: items['total'] \
            for items in balances \
            if items['coin'] in coins
        }
    
    def get_min_provide_size(self):
        return float(self.get_market(self.symbol)['minProvideSize'])
    
    def get_size_increment(self):
        return float(self.get_market(self.symbol)['sizeIncrement'])

    def get_price_increment(self):
        return float(self.get_market(self.symbol)['priceIncrement'])

class ClassicFuture(FtxClient):
    def __init__(self, api_key, api_secret, subaccount_name=None, symbol=None, postOnly=False):
        super().__init__(api_key, api_secret, subaccount_name)
        self.api_key = api_key
        self.api_secret = api_secret
        self.subaccount = subaccount_name
        self.symbol = symbol
        self.postOnly = postOnly
    
    def get_price(self):
        return float(self.get_market(self.symbol)['price'])
    
    def get_previous_price(self): 
        orders = self.get_fills(self.symbol)
        if not orders:
            return float(1000000)
        return float(orders[0]['price'])

    def set_leverage(self, lev):
        return super().set_leverage(lev)
    
    def get_position_size(self):
        position = self.get_position()
        pos_size = [pos['netSize'] for pos in position if pos['future'] == self.symbol]
        return float(0) if not pos_size else float(pos_size[0])
    
    def create_order(self, side, price, types, size):
        try:
            return self.place_order(self.symbol, side, price, types, size, postOnly=self.postOnly)
        except Exception as err:
            return f'ERROR: {err}'
    
    def get_pending_order(self):
        return super().get_pending_order(self.symbol)
    
    def cancel_all_symbol_orders(self):
        orders = self.get_pending_order()
        if not orders: 
            return 'No orders for cancel'
        else:
            for order in orders:
                self.cancel_order(float(order['id']))
            return 'Orders queued for cancellation'
    
    def get_national_size(self):
        position = self.get_position()
        national_size = [pos['cost'] for pos in position if pos['future'] == self.symbol]
        return float(0) if not national_size else float(national_size[0])
        
    def est_liquidation_price(self):
        position = self.get_position()
        liq_price = [pos['estimatedLiquidationPrice'] for pos in position \
                if pos['future'] == self.symbol]
        if not liq_price:
            return float(0) 
        else:
            liq_price = liq_price[0]
            return float(0) if liq_price is None else float(liq_price)
    
    def get_total_collateral(self):
        return float(self.get_account()['collateral'])
    
    def get_free_collateral(self):
        return float(self.get_account()['freeCollateral'])

    def get_maintenance_margin(self):
        return float(self.get_account()['maintenanceMarginRequirement'])
    
    def get_leverage(self):
        return float(self.get_account()['leverage'])
    
    def get_leverage_used(self):
        total_pos_size = float(self.get_account()['totalPositionSize'])
        account_value = float(self.get_account()['totalAccountValue'])
        return float(total_pos_size/account_value)

    def get_min_provide_size(self):
        return float(self.get_market(self.symbol)['minProvideSize'])
    
    def get_size_increment(self):
        return float(self.get_market(self.symbol)['sizeIncrement'])

    def get_price_increment(self):
        return float(self.get_market(self.symbol)['priceIncrement'])
    
    def cal_margin_used(self, price, position, leverage):
        margin = price*position/leverage
        return float(margin)    

    def cal_funding_payments(self, side):
        cost = 0
        funding_payments = self.get_funding_payments()   
        for payment in funding_payments:
            if payment['future'] == self.symbol:
                cost += payment['payment']

        return -1*float(cost) if side == 'long' else float(cost) 

if __name__ == '__main__':

    pass


    

    

  


