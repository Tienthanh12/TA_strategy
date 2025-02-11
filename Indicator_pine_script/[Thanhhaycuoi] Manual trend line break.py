// This Pine Script™ code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © trantienthanh1208


//@version=5
indicator("[Thanhhaycuoi] Manual draw trend line","TLB",overlay = true, max_labels_count = 500, max_lines_count = 500)

// SETTINGS {  
string entry_long_mess ='Tradingview Alert\n' + syminfo.tickerid +  '\nSignal: Long\nPrice = ' + str.tostring(close) 

string entry_short_mess ='Tradingview Alert\n' + syminfo.tickerid +  '\nSignal: Short\nPrice = ' + str.tostring(close) 
        

x_chan_top_x1 = input.time(timestamp('January 1, 2024'), 'Top Left', inline = 'TOP1', group = 'Coordinates', confirm = true)
x_chan_top_x1_c = input.color(color.blue, '', inline = 'TOP1', group = 'Coordinates')
x_chan_top_x2 = input.time(timestamp('January 1, 2024'), 'Top Right', inline = 'TOP2', group = 'Coordinates', confirm = true)
x_chan_top_x2_c = input.color(color.blue, '', inline = 'TOP2', group = 'Coordinates')

x_chan_btm_x1 = input.time(timestamp('January 1, 2024'), 'Bottom Left', inline = 'BOTTOM1', group = 'Coordinates', confirm = true)
x_chan_btm_x1_c = input.color(color.orange, '', inline = 'BOTTOM1', group = 'Coordinates')
x_chan_btm_x2 = input.time(timestamp('January 1, 2024'), 'Bottom Right', inline = 'BOTTOM2', group = 'Coordinates', confirm = true)
x_chan_btm_x2_c = input.color(color.orange, '', inline = 'BOTTOM2', group = 'Coordinates')

x_chan_nm_use = input.bool(false, 'Show Names', group = 'Coordinates')
x_chan_hand_use = input.bool(false, 'Show Handles', group = 'Coordinates')


x_chan_end_tm_use = input.bool(false, 'End Date/Time', inline = 'END', group = 'Adjustments')
x_chan_end_tm = input.time(timestamp('January 2, 2024'), '', inline = 'END', group = 'Adjustments')
x_chan_end_tm_c = input.color(color.red, '', inline = 'END', group = 'Adjustments')

x_chan_top_cxo_use = input.bool(true, 'Exit Channel Top', inline = 'EXITTOP', group = 'Markers')
x_chan_top_cxo_c = input.color(color.blue, '', inline = 'EXITTOP', group = 'Markers')
x_chan_top_cxu_use = input.bool(true, 'Enter Channel Top', inline = 'ENTERTOP', group = 'Markers')
x_chan_top_cxu_c = input.color(#6c5ce7, '', inline = 'ENTERTOP', group = 'Markers')
x_chan_btm_cxo_use = input.bool(true, 'Enter Channel Bottom', inline = 'ENTERBOTTOM', group = 'Markers')
x_chan_btm_cxo_c = input.color(#d35400, '', inline = 'ENTERBOTTOM', group = 'Markers')
x_chan_btm_cxu_use = input.bool(true, 'Exit Channel Bottom', inline = 'EXITBOTTOM', group = 'Markers')
x_chan_btm_cxu_c = input.color(color.orange, '', inline = 'EXITBOTTOM', group = 'Markers')
mmt_candle_use = input.bool(true,"momentum bar", inline = "mmt_bar", group = "Markers")
mmt_candle_c = input.color(color.white, '', inline = 'mmt_bar', group = 'Markers')
x_chan_cx_cons_use = input.bool(false, 'Allow Consecutive Markers', tooltip = 'When enabled, multiple markers of the same kind can fire in a row.', group = 'Markers')


length_1 = input.int(200, "MA length",group = "setting")
length_2 = input.int(title="ATR Length", defval=10, minval=1,group = "setting")
smoothing = input.string(title="Smoothing", defval="SMA", options=["RMA", "SMA", "EMA", "WMA"], group = "setting")
MmtRatio_rf = input.float(1.8, 'Ratio Reference', inline = 'Momentum candle',group = "setting" )
bodyscale_rf = input.float(0.65, 'Scale Reference', inline = 'Momentum candle',group = "setting" )
// }

// function {
ma_function(source, length) =>
	switch smoothing
		"RMA" => ta.rma(source, length)
		"SMA" => ta.sma(source, length)
		"EMA" => ta.ema(source, length)
		=> ta.wma(source, length)

//Non-repainting security function 
RequestSecurityNRP(_tf, _exp, _barmerge) =>
    request.security(syminfo.tickerid, _tf , _exp[barstate.isrealtime ? 1 : 0], _barmerge)[barstate.isrealtime ? 0 : 1]


isMomentumbar(float TR_ratio,float TR_ration_reference,float Body_scale, float Body_scale_reference) =>
	TR_ratio >= TR_ration_reference and Body_scale >= Body_scale_reference 

//}

SMA200_1h = RequestSecurityNRP("60", ma_function(close, length_1), barmerge.gaps_on)
SMA200_1h_no_na = fixnan(SMA200_1h)

float TR_value = ta.tr(true)
float ATR_value = ma_function(TR_value, length_2)
float TR_ratio = TR_value / ATR_value
float Body = math.abs(close - open)
float Body_scale = Body / (high - low)

// Handles
var line hand_top_x1_ln = x_chan_hand_use ? line.new(x_chan_top_x1, high, x_chan_top_x1, low, xloc.bar_time, extend.both, color.new(x_chan_top_x1_c, 60), line.style_dotted, 3) : na
var line hand_top_x2_ln = x_chan_hand_use ? line.new(x_chan_top_x2, high, x_chan_top_x2, low, xloc.bar_time, extend.both, color.new(x_chan_top_x2_c, 60), line.style_dotted, 3) : na
var line hand_btm_x1_ln = x_chan_hand_use ? line.new(x_chan_btm_x1, high, x_chan_btm_x1, low, xloc.bar_time, extend.both, color.new(x_chan_btm_x1_c, 60), line.style_dotted, 3) : na
var line hand_btm_x2_ln = x_chan_hand_use ? line.new(x_chan_btm_x2, high, x_chan_btm_x2, low, xloc.bar_time, extend.both, color.new(x_chan_btm_x2_c, 60), line.style_dotted, 3) : na

// Coordinates
var label xy_top_tl = label.new(na, na, '⏺', xloc.bar_index, yloc.price, color(na), label.style_label_center, x_chan_top_x1_c, size.normal)
var label xy_top_tr = label.new(na, na, '⏺', xloc.bar_index, yloc.price, color(na), label.style_label_center, x_chan_top_x2_c, size.normal)
var label xy_btm_bl = label.new(na, na, '⏺', xloc.bar_index, yloc.price, color(na), label.style_label_center, x_chan_btm_x1_c, size.normal)
var label xy_btm_br = label.new(na, na, '⏺', xloc.bar_index, yloc.price, color(na), label.style_label_center, x_chan_btm_x2_c, size.normal)

// Coordinates labels
var label xy_top_tl_nm = x_chan_nm_use ? label.new(na, na, 'TL', xloc.bar_index, yloc.abovebar, color(na), label.style_label_center, chart.fg_color, size.small, tooltip = 'Top Left', text_font_family = font.family_monospace) : na
var label xy_top_tr_nm = x_chan_nm_use ? label.new(na, na, 'TR', xloc.bar_index, yloc.abovebar, color(na), label.style_label_center, chart.fg_color, size.small, tooltip = 'Top Right', text_font_family = font.family_monospace) : na
var label xy_btm_bl_nm = x_chan_nm_use ? label.new(na, na, 'BL', xloc.bar_index, yloc.belowbar, color(na), label.style_label_center, chart.fg_color, size.small, tooltip = 'Bottom Left', text_font_family = font.family_monospace) : na
var label xy_btm_br_nm = x_chan_nm_use ? label.new(na, na, 'BR', xloc.bar_index, yloc.belowbar, color(na), label.style_label_center, chart.fg_color, size.small, tooltip = 'Bottom Right', text_font_family = font.family_monospace) : na

// Channel lines {
var line chan_top_ln = line.new(na, na, na, na, xloc.bar_index, extend.none, #c23eda, line.style_dashed, 1)
var line chan_btm_ln = line.new(na, na, na, na, xloc.bar_index, extend.none, #c23eda, line.style_dashed, 1)
var line chan_top_ext_ln = line.new(na, na, na, na, xloc.bar_index, extend.none, chart.fg_color, line.style_dashed, 1)
var line chan_btm_ext_ln = line.new(na, na, na, na, xloc.bar_index, extend.none, chart.fg_color, line.style_dashed, 1)

var linefill chan_lf = linefill.new(chan_top_ln, chan_btm_ln, color.new(color.purple, 90))
var chan_ext_lf = linefill.new(chan_top_ext_ln, chan_btm_ext_ln, color.new(color.purple, 90))

// End Date/Time {
in_end_tm = (x_chan_end_tm_use and time <= x_chan_end_tm) or not x_chan_end_tm_use

var line end_ln = x_chan_end_tm_use ? line.new(na, na, na, na, xloc.bar_index, extend.both, x_chan_end_tm_c, line.style_dashed, 1) : na

if time >= x_chan_end_tm and time[1] < x_chan_end_tm
    end_ln.set_xy1(bar_index, high)
    end_ln.set_xy2(bar_index, low)
// }

if ta.change(time >= x_chan_top_x1)
    chan_top_ln.set_xy1(bar_index, high)

    xy_top_tl.set_xy(bar_index, high)
    xy_top_tl_nm.set_xy(bar_index, high)

if ta.change(time >= x_chan_top_x2)
    chan_top_ln.set_xy2(bar_index, high)

    chan_top_ext_ln.set_xy1(bar_index, high)
    chan_top_ext_ln.set_xy2(last_bar_index + 20, chan_top_ln.get_price(last_bar_index + 20))

    xy_top_tr.set_xy(bar_index, high)
    xy_top_tr_nm.set_xy(bar_index, high)


if ta.change(time >= x_chan_btm_x1)
    chan_btm_ln.set_xy1(bar_index, low)

    xy_btm_bl.set_xy(bar_index, low)
    xy_btm_bl_nm.set_xy(bar_index, low)

if ta.change(time >= x_chan_btm_x2)
    chan_btm_ln.set_xy2(bar_index, low)

    chan_btm_ext_ln.set_xy1(bar_index, low)
    chan_btm_ext_ln.set_xy2(last_bar_index + 20, chan_btm_ln.get_price(last_bar_index + 20))

    xy_btm_br.set_xy(bar_index, low)
    xy_btm_br_nm.set_xy(bar_index, low)

// CROSSES {
var bool top_cxo = false
var bool top_cxu = false
var bool btm_cxo = false
var bool btm_cxu = false
var bool buy_signal = false 
var bool sell_signal = false 
bool mmtbar = isMomentumbar(TR_ratio, MmtRatio_rf, Body_scale, bodyscale_rf )


if x_chan_cx_cons_use
    top_cxo := false
    top_cxu := false
    btm_cxo := false
    btm_cxu := false

top_cxo := ta.crossover(close, chan_top_ln.get_price(bar_index)) and in_end_tm ? true : top_cxo
top_cxu := ta.crossunder(close, chan_top_ln.get_price(bar_index)) and in_end_tm ? true : top_cxu
btm_cxo := ta.crossover(close, chan_btm_ln.get_price(bar_index)) and in_end_tm ? true : btm_cxo
btm_cxu := ta.crossunder(close, chan_btm_ln.get_price(bar_index)) and in_end_tm ? true : btm_cxu

if barstate.isconfirmed
    buy_signal := close >= SMA200_1h_no_na and top_cxo and close > open and mmtbar ? true : buy_signal
    sell_signal := close <= SMA200_1h_no_na and btm_cxu and close < open and mmtbar ? true : sell_signal

top_cxo_new = top_cxo and not top_cxo[1]
top_cxu_new = top_cxu and not top_cxu[1]
btm_cxo_new = btm_cxo and not btm_cxo[1]
btm_cxu_new = btm_cxu and not btm_cxu[1]
bool buy_signal_new = buy_signal and not buy_signal[1]
bool sell_signal_new = sell_signal and not sell_signal[1]


top_cxo := top_cxu_new or btm_cxu_new ? false : top_cxo
top_cxu := top_cxo_new or btm_cxo_new ? false : top_cxu
btm_cxo := btm_cxu_new or top_cxu_new ? false : btm_cxo
btm_cxu := btm_cxo_new or top_cxo_new ? false : btm_cxu
buy_signal := not top_cxo and sell_signal_new ? false : buy_signal
sell_signal := not btm_cxu and buy_signal_new ? false : sell_signal


end_tm = x_chan_end_tm_use and not in_end_tm and in_end_tm[1]
// draw candle movement 
if x_chan_top_cxo_use and top_cxo_new
    label.new(bar_index, chan_top_ln.get_price(bar_index), '⬆', xloc.bar_index, yloc.abovebar, na, label.style_label_center, x_chan_top_cxo_c, size.small) 

if x_chan_top_cxu_use and top_cxu_new
    label.new(bar_index, chan_top_ln.get_price(bar_index), '⬇', xloc.bar_index, yloc.belowbar, na, label.style_label_center, x_chan_top_cxu_c, size.small)

if x_chan_btm_cxo_use and btm_cxo_new
    label.new(bar_index, chan_btm_ln.get_price(bar_index), '⬆', xloc.bar_index, yloc.abovebar, na, label.style_label_center, x_chan_btm_cxo_c, size.small)

if x_chan_btm_cxu_use and btm_cxu_new
    label.new(bar_index, chan_btm_ln.get_price(bar_index), '⬇', xloc.bar_index, yloc.belowbar, na, label.style_label_center, x_chan_btm_cxu_c, size.small)

// draw momentum candle signal 
if mmt_candle_use and mmtbar
    label.new(bar_index, close,"🦈", xloc.bar_index, yloc.abovebar, na, label.style_label_center, mmt_candle_c, size.tiny)  


// Draw the buy/sell signal and alert
if buy_signal_new
    label.new(bar_index, close, "Buy", xloc.bar_index, yloc.belowbar, color.green, label.style_triangleup, color.white, size.tiny)
    log.info(entry_long_mess)
    alert(entry_long_mess,alert.freq_once_per_bar)

if sell_signal_new
    label.new(bar_index, close, "Sell", xloc.bar_index, yloc.abovebar, color.red, label.style_triangledown, color.white, size.tiny)
    log.info(entry_short_mess)
    alert(entry_short_mess, alert.freq_once_per_bar)

// Adjust channel at End Date/Time.
if end_tm or chan_top_ext_ln.get_price(bar_index) <= chan_btm_ext_ln.get_price(bar_index)
    chan_top_ext_ln.set_y2(chan_top_ext_ln.get_price(bar_index))
    chan_top_ext_ln.set_x2(bar_index)
    chan_top_ext_ln.set_extend(extend.none)

    chan_btm_ext_ln.set_y2(chan_btm_ext_ln.get_price(bar_index))
    chan_btm_ext_ln.set_x2(bar_index)
    chan_btm_ext_ln.set_extend(extend.none)
// }


// PLOTS {
plot(chan_top_ext_ln.get_price(bar_index), 'Channel Top', x_chan_top_x1_c, display = display.data_window)
plot(chan_btm_ext_ln.get_price(bar_index), 'Channel Bottom', x_chan_btm_x1_c, display = display.data_window)
plot(TR_ratio, 'True Range Ratio', color.white, display = display.data_window, precision = 2)
plot(Body_scale, 'Body Scale', color.white, display = display.data_window, precision = 2)

plot(chan_btm_ext_ln.get_price(bar_index), 'Channel Bottom', x_chan_btm_x1_c, display = display.data_window)

plot(SMA200_1h, "SMA200_1h", (color.yellow), linewidth = 1)



