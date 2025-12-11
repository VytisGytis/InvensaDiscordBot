import wbgapi as wb
import pandas as pd
import matplotlib.pyplot as plt
import sarasai
from Dictonaries import WBGAPI_serijos
from datetime import date


GDP =  'NY.GDP.MKTP.KD' #GDP serijos
GDPPC = 'NY.GDP.PCAP.KD' #GDP per capita serijos
CPI = 'FP.CPI.TOTL.ZG' #Infliacija
FDI = 'BX.KLT.DINV.WD.GD.ZS' #Užsienio tiesioginės investicijos

# List all available series
#for s in wb.series.list():
#    print(s['id'], "-", s['value'])

country = 'USA'
year = 2012

popul = wb.data.get('SP.POP.TOTL', country, time = year)
populiacija = popul['value']
    
    #await ctx.send(f'{country} populiacija {year} metais: {populiacija}')
print(popul)


args = ['USA', 'LTU', 'GDP', 'GDPPC']


axis = []
years = []
salis = []

for arg in args:
    if arg.isdigit() == False:
        if arg in sarasai.WBGAPI_Rodikliai:
            axis.append(WBGAPI_serijos[arg])
        elif arg in sarasai.Saliu_Pavadinimai:
            salis.append(arg)
        else:
            print(f'Neatpažintas argumentas: {arg}')
    else:
        years.append(int(arg))
    
if len(axis) > 2:
    print('Parašyta per daug rodiklių. Plot\'insim tik pirmus du rodiklius')
elif len(axis) == 0:   
    print('Nėra rodiklio(-ių), prašau įrašykite rodiklį(-ius)')
        

if len(salis) == 0:
    print('Nėra šalies(-ių), prašau įrašykite šalį(-is)')
        

if len(years) == 0:
    print('Neparašyti metai. Plot\'insim nuo 2000 iki dabar')
    years = [2000, date.today().year]

print(axis)
print(salis)
print(years)
    
duomenysPirmi = wb.data.DataFrame(axis, salis[0], range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
duomenysPirmi = pd.DataFrame(duomenysPirmi)

duomenysAntri = wb.data.DataFrame(axis, salis[1], range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
duomenysAntri = pd.DataFrame(duomenysPirmi)

    #duomenysPirmi.rename(columns = {'NY.GDP.MKTP.KD' : 'GDP', 'HD.HCI.OVRL' : 'HCI', 'NY.GDP.PCAP.KD' : 'GDPPC', 'FP.CPI.TOTL.ZG' : 'CPI', 'BX.KLT.DINV.WD.GD.ZS' : 'FDI'}, inplace = True)
    #print(duomenysPirmi)

duomenysPirmi = duomenysPirmi.sort_values(by = ['Time'], ascending = True)
duomenysAntri = duomenysAntri.sort_values(by = ['Time'], ascending = True)

Grafas, ax = plt.subplots()
ax2 = ax.twinx()

Graphtitle = axis[0] + ' ir ' + axis[1] + ': ' + salis[0]

ax.plot(duomenysPirmi.index.values, duomenysPirmi[axis[0]], color = 'green', label = axis[0])
ax.set(xlabel = "Metai", ylabel = axis[0],  title = Graphtitle)

ax2.plot(duomenysPirmi.index.values, duomenysPirmi[axis[1]], color = 'black', label = axis[1])
ax2.set_ylabel(axis[1])

Grafas.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)

    #plt.legend(['GDP', 'GDP per Capita'])
plt.savefig('MDG_GDP.png', dpi = 400)

#Grafas2, ax = plt.subplots()

