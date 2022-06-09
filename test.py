   
counter = 0
orderIdAvgBuyPrice = {}
sellbound = 0.25
dcabound = 0.15

if len(orderIdAvgBuyPrice) > counter:
    if sellbound > 0.1:
        sellbound = sellbound / 1.1**len(orderIdAvgBuyPrice)
    if len(orderIdAvgBuyPrice) > counter:
        dcabound = dcabound * 1.15**len(orderIdAvgBuyPrice)
    counter +=1



orderIdAvgBuyPrice['hi'] = 1
orderIdAvgBuyPrice['s'] = 2
print(sellbound)