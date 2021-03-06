from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    Util,
)
from vnpy.app.cta_strategy.NewStrategyBody import StrategyBody

class MyStrategy(CtaTemplate):

    author = 'Anonymous'

    fast_window = 10
    slow_window = 20
    security = ''
    frequency = '28m'
    onlyDuo = 0
    onlyKon = 0
    trade_position = 1
    enableTrade = 1
    use_persisted_prop = 0

    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters = ['security', 'frequency', 'onlyDuo', 'onlyKon', 'trade_position', 'use_persisted_prop']
    variables = ['fast_ma0', 'fast_ma1', 'slow_ma0', 'slow_ma1']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(MyStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )
        self.security = Util.get_JQ_Format_name(self.security)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.put_event()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.nsb = StrategyBody(security=self.security, frequency=self.frequency, onlyDuo=self.onlyDuo,
                                onlyKon=self.onlyKon,
                                enableSendMessage=True, trade_position=self.trade_position, use_persisted_prop=(self.use_persisted_prop == 1), trader=self)
        self.write_log("策略on_init - jqdatasdk security: " + str(self.nsb.security))
        self.write_log("策略on_init - jqdatasdk frequency: " + str(self.nsb.frequency))
        self.write_log("策略on_init - jqdatasdk onlyDuo: " + str(self.nsb.onlyDuo))
        self.write_log("策略on_init - jqdatasdk onlyKon: " + str(self.nsb.onlyKon))
        self.write_log("策略on_init - jqdatasdk enableSendMessage: " + str(self.nsb.enableSendMessage))
        self.write_log("策略on_init - jqdatasdk trade_position: " + str(self.nsb.trade_position))
        self.write_log("策略on_init - jqdatasdk trader: " + str(self.nsb.trader is not None))
        self.put_event()

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.nsb = StrategyBody(security=self.security, frequency=self.frequency, onlyDuo=self.onlyDuo,
                                onlyKon=self.onlyKon,
                                enableSendMessage=True, trade_position=self.trade_position, use_persisted_prop=(self.use_persisted_prop == 1), trader=self)
        self.write_log("策略on_start - jqdatasdk security: " + str(self.nsb.security))
        self.write_log("策略on_start - jqdatasdk frequency: " + str(self.nsb.frequency))
        self.write_log("策略on_start - jqdatasdk onlyDuo: " + str(self.nsb.onlyDuo))
        self.write_log("策略on_start - jqdatasdk onlyKon: " + str(self.nsb.onlyKon))
        self.write_log("策略on_start - jqdatasdk enableSendMessage: " + str(self.nsb.enableSendMessage))
        self.write_log("策略on_start - jqdatasdk trade_position: " + str(self.nsb.trade_position))
        self.write_log("策略on_start - jqdatasdk trader: " + str(self.nsb.trader is not None))
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.nsb.setPosition(position=0)
        self.nsb.setOpen(open=0)
        self.nsb.setReal_Open(real_open=0)
        self.nsb.open_after_next_change = False
        self.write_log("策略on_stop - 状态已清空")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        if self.nsb is None:
            self.on_start()
        self.nsb.handleOneTick(nowTimeString=Util.getYMDHMS(), tick=tick)
        self.write_log(str(Util.getYMDHMS()) + ": " + str(tick.last_price))
        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass