import discord
from discord.ext import commands, tasks
from datetime import date
import matplotlib.pyplot as plt

import wbgapi as wb
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import requests
from bs4 import BeautifulSoup
from openbb import obb

import sarasai
from Dictonaries import WBGAPI_serijos
from Dictonaries import kompanijos
from Dictonaries import country_codes
from CompInfoDump import*

from numerize import numerize

from dotenv import load_dotenv
import aiosqlite
import re
import os

#========================Dovydas======================#
DATABASE_FILE = 'discord_bot.db'

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)
admin_role = "Admin"
user_role = "User"
notified_role = "Alert"
alert_channel = "alerts"

url_pattern = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)
spans = ["second", "seconds", "minute", "minutes", "hour", "hours", "day", "days", "week", "weeks", "month", "months", "year", "years"]

def extract_links(text):
    return url_pattern.findall(text)

@bot.event
async def on_ready():
    print(f"Roger Dodger, {bot.user.name}")
    
    if not check_reminders.is_running():
        check_reminders.start()

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return

        
    links = extract_links(msg.content)
            
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            await db.execute("""
                INSERT INTO user_logs (user_id)
                VALUES (?)
            """, (str(msg.author.id),))
            await db.commit()
            
            if links:
                for i in links:
                    await db.execute("""
                        INSERT INTO links (user_id, resource_url)
                        VALUES (?, ?)
                    """, (str(msg.author.id), i))
                    await db.commit()
        except Exception as e:
            print(f"Database error in on_message: {e}")
    await bot.process_commands(msg)

@bot.command()
async def remindme(ctx, *, msg):
    
    fail = False
    try:
        args, text = msg.split(":", 1)
    except:
        args = msg
        fail = True

    time, span = args.split(" ")

    if fail:
        text = f'Prašei priminti prieš {time} {span}'
    
    if (time.isnumeric() == False) or (span not in spans):
        await ctx.send("Bad arguments. Use /remindme [time] [span]: [message]")
        return
    
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            
            if span in ["weeks", "week"]:
                span = "days"
                time = int(time)*7
            await db.execute("""
                INSERT INTO user_messages (user_id, message_date, message_text, is_complete)
                VALUES (?, DATETIME('now', '+{} {}'), ?, 0)
            """.format(time, span), (str(ctx.author.id), text))
            await db.commit()
            await ctx.send("Reminder set for {} {} from now".format(time, span))
        except Exception as e:
            await ctx.send(f"Database error in remindme: {e}")


@tasks.loop(minutes=1.0)
async def check_reminders():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            cursor = await db.execute("""
                SELECT rowid, user_id, message_text
                FROM user_messages
                WHERE message_date <= DATETIME('now') AND is_complete = 0
            """)
            
            to_send = await cursor.fetchall()
            
            if not to_send:
                return
                
            for rowid, username, message_text in to_send:
                user = await bot.fetch_user(username)
                await user.send(message_text)
                
                await db.execute("""
                    UPDATE user_messages
                    SET is_complete = 1
                    WHERE rowid = ?
                """, (rowid,))
                await db.commit()
            
        except Exception as e:
            print(f"Database error in check_reminders: {e}")
            
@bot.command()
@commands.has_role(admin_role)
async def adduser(ctx, user: discord.Member, *, msg):
    user_id = user.id
    
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            await db.execute("""
                INSERT INTO users (user_id, username)
                VALUES (?, ?)
            """, (user_id, msg))
            await db.commit()
            await ctx.guild.get_member(user_id).edit(nick=msg)
            role = discord.utils.get(ctx.guild.roles, name=user_role)
            await user.add_roles(role)
            await ctx.send("{} added as {}".format(user, msg))
        except Exception as e:
            await ctx.send(f"Database error in adduser: {e}")
    
@bot.command()
@commands.has_role(admin_role)
async def addname(ctx, *, msg):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        try:
            await db.execute("""
                INSERT INTO users (user_id, username)
                VALUES (?, ?)
            """, (0, msg))
            await db.commit()
            await ctx.send("{} has been added to the members list".format(msg))
        except Exception as e:
            await ctx.send(f"Database error in has_role: {e}")
    
@bot.command()
async def join(ctx, *, msg):
    role = discord.utils.get(ctx.guild.roles, name=user_role)
    if role not in ctx.author.roles:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            try:
                cursor = await db.execute("""
                    SELECT username
                    FROM users
                    WHERE user_id = 0 AND username = ? 
                """, (msg,))
                name = await cursor.fetchone()
                if name is None:
                    await ctx.send(f"{msg} is not in the expected users list")
                    return
                name = name[0]
                
                await db.execute("""
                    UPDATE users
                    SET user_id = ?
                    WHERE username = ?
                """, (ctx.author.id, name))
                await db.commit()
                
                await ctx.author.edit(nick=name)
                role = discord.utils.get(ctx.guild.roles, name=user_role)
                await ctx.author.add_roles(role)
            except Exception as e:
                await ctx.send(f"Database error in join: {e}")
    else:
        await ctx.send(f"{ctx.author.mention} already has the {user_role} role")
        return
    
@bot.command()
async def joinrequest(ctx):
    role = discord.utils.get(ctx.guild.roles, name=user_role)
    channel_id = discord.utils.get(ctx.guild.channels, name=alert_channel).id
    channel = bot.get_channel(channel_id)
    role = discord.utils.get(ctx.guild.roles, name=notified_role).id
    if role not in ctx.author.roles:
        await ctx.send("Moderators have been notified of your request")
        await channel.send(f"<@&{role}>, {ctx.author.mention} is requesting to join")
    else:
        await ctx.send(f"{ctx.author.mention} already has the {user_role} role")
        return
            
@check_reminders.before_loop
async def before_check_reminders():
    await bot.wait_until_ready()
#========================Dovydas======================#
#========================Vytis========================#

async def sortArgs(ctx, args): #sortina salies info

    args = args.split(' ')  

    axis = []
    pavadinimai = []
    years = []
    salis = []
    saliscode = []
    pervadinimai = {}
    lyginimas  = False
    change = False
    pavadinimaiChange = []

    for arg in args:
        if arg.isdigit() == False:
            if arg.upper() in sarasai.WBGAPI_Rodikliai:
                pavadinimai.append(arg)
                pavadinimaiChange.append(arg)
                axis.append(WBGAPI_serijos[arg.upper()])
                pervadinimai[WBGAPI_serijos[arg.upper()]] = arg
            elif arg.lower() in country_codes:
                salis.append(arg)
                saliscode.append(country_codes[arg.lower()])
            elif arg.lower() in ['pokytis', 'change', '%']:
                change = True
            elif arg.lower() in ['palyginti', 'vs', 'compare', 'palygink']:
                lyginimas = True
            elif arg.lower() in ['basic', 'all', 'visa', 'visas']:
                for rodiklis in sarasai.WBGAPI_Rodikliai:
                    pavadinimai.append(rodiklis)
                    pavadinimaiChange.append(rodiklis)
                    axis.append(WBGAPI_serijos[rodiklis])
                    pervadinimai[WBGAPI_serijos[rodiklis]] = rodiklis
            else:
                await ctx.send(f'Neatpažintas argumentas: {arg}')

        else:
            if int(arg) <= date.today().year:
                years.append(int(arg))
            else: 
                years.append(int(date.today().year))

    return axis, pavadinimai, years, salis, saliscode, pervadinimai, lyginimas, change, pavadinimaiChange




async def sortCompArgs(ctx, msg):  #sortina kompanijos info

    tickeriai = []
    pavadinimai = []
    years = []
    ratios = []
    tinkama = True
    

    try:
        kompanijos, info = msg.split(':', 1)
    except:
        kompanijos = msg
        info = ''
    for kompanija in kompanijos.split(','):
        pavadinimas = ''
        for word in kompanija.split(' '):
            if word.isupper():
                tickeriai.append(word)
            else:
                pavadinimas = pavadinimas + ' ' + word
        if pavadinimas != '':
            pavadinimai.append(pavadinimas.strip())
        else:
            try:
                pavadinimai.append(tickeriai[-1])
            except:
                await ctx.send(f'Nėra ticker\'io arba jis parašytas mažosiomis raidėmis naudokite formatą: /[komanda] [TICKER] [kompanija], [TICKER2] [kompanija]')
                tinkama = False
                return [], [], [], [], tinkama


    if len(tickeriai) == 0:
        await ctx.send(f'Nėra ticker\'io arba jis parašytas mažosiomis raidėmis naudokite formatą: /[komanda] [TICKER] [kompanija], [TICKER2] [kompanija]')
        tinkama = False
        return [], [], [], [], tinkama


    if info != '':
        for ratio in info.split(','):
            if ratio.isdigit():
                years.append(int(ratio))
            elif ratio.strip().lower() in sarasai.RatioSar:
                ratios.append(ratio.strip().lower())
            else:
                await ctx.send(f'Neatpažintas argumentas: {ratio.strip()}')
    else:
        ratios = []

    return tickeriai, pavadinimai, years, ratios, tinkama




    



plt.style.use('dark_background')

file_path = os.path.dirname(__file__)




@bot.command(name = 'info')
async def info(ctx, *, args):

    axis, pavadinimai, years, salis, saliscode, pervadinimai, lyginimas, change, pavadinimaiChange = await sortArgs(ctx, args)
    
    #print(axis, pavadinimai, years, salis, ' viduj')

    if len(salis) == 0 or len(axis) == 0:
        await ctx.send('Nėra šalies(-ių) arba rodiklio(-ių), prašau įrašykite šalį(-is) ir rodiklį(-ius)')
        return

    if len(salis) == 1:
        embed = discord.Embed(title="Šalies info:", colour=discord.Colour.default())
    else: 
        embed = discord.Embed(title="Šalių info:", colour=discord.Colour.default())

    if years == []:
        years.append(int(date.today().year)-1)
    
    if len(years) > 1:
        years = [min(years), max(years)]
        if max(years) >= date.today().year:
            years[1] = date.today().year-1

    if len(salis) != 0:
        for sal, code in zip(salis, saliscode):

            emoji = code['alpha2'].lower()
            Ftitle = sal.replace('_', ' ').capitalize() + f' :flag_{emoji}:'
            Vinfo = ''

            for pav, ax in zip(pavadinimai, axis):
                try:
                    kintamas = wb.data.get(ax, code['alpha3'], time = max(years))
                    kintamas = kintamas['value']
                    if len(years) != 1:
                        try:
                            antraskintamas = wb.data.get(ax, code['alpha3'], time = min(years))
                            antraskintamas = antraskintamas['value']
                            if change == True:
                                pokytis = ((kintamas - antraskintamas) / antraskintamas) * 100
                                Vinfo = Vinfo + f'{pav}: {min(years)} -> {numerize.numerize(antraskintamas)}, {max(years)} -> {numerize.numerize(kintamas)}, pakito {round(pokytis, 2)} %\n'
                            else:
                                Vinfo = Vinfo + f'{pav}: {min(years)} -> {numerize.numerize(antraskintamas)}, {max(years)} -> {numerize.numerize(kintamas)}\n'
                        except:
                            Vinfo = Vinfo + f'{pav}: {min(years)} -> duomenų nerasta, {max(years)} -> {numerize.numerize(kintamas)}\n'

                    else:
                        Vinfo = Vinfo + f'{pav}: {max(years)} -> {numerize.numerize(kintamas)}\n'
                except:
                    await ctx.send(f'Rodiklio {pav} duomenų nerasta {sal} šaliai {max(years)} metais')
            
            embed.add_field(name = Ftitle, value = Vinfo)

        await ctx.send(embed=embed)


@bot.command(name = 'plot') #grafikai iš wbgapi
async def plot(ctx, *, args):

    axis, pavadinimai, years, salis, saliscode, pervadinimai, lyginimas, change, pavadinimaiChange = await sortArgs(ctx, args)


    spalvos =['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',]

    
    if len(axis) > 2:
        await ctx.send('Parašyta per daug rodiklių. Plot\'insim tik pirmus du rodiklius')
    elif len(axis) == 0:   
        await ctx.send('Nėra rodiklio(-ių), prašau įrašykite rodiklį(-ius)')
        return

    if len(salis) == 0:
        await ctx.send('Nėra šalies(-ių), prašau įrašykite šalį(-is)')
        return

    if len(years) == 0:
        await ctx.send('Neparašyti metai. Plot\'insim nuo 2000 iki dabar')
        years = [2000, date.today().year]
    elif len(years) == 1:
        years = [years[0], date.today().year]

    


    Grafas, ax = plt.subplots()
    plt.grid()

    for sal, code in zip(salis, saliscode):
        
        file_path = os.path.join(os.path.dirname(__file__), 'Grafas.png')
        
        if os.path.exists(file_path):
            os.remove(file_path)
            

        try:
            duomenys = wb.data.DataFrame(axis, code['alpha3'], range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
            duomenys = pd.DataFrame(duomenys)
        except: 
            years = [2000, date.today().year]
            duomenys = wb.data.DataFrame(axis, code['alpha3'],  range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
            duomenys = pd.DataFrame(duomenys)
            await ctx.send('Neegzistuojantis metai. Plot\'insim nuo 2000 iki dabar')

        duomenys.rename(columns = pervadinimai, inplace = True)
        
        if change == True:
            for i in range(len(pavadinimai)):
                duomenys[pavadinimai[i]+' pokytis %'] = duomenys[pavadinimai[i]].pct_change(-1).mul(100)
                if sal == salis[0]:
                    pavadinimaiChange[i] = pavadinimai[i] + ' pokytis %'

        duomenys = duomenys.sort_values(by = ['Time'], ascending = True)

        if lyginimas == False:
            Grafas, ax = plt.subplots()
            plt.grid()


        if change == False:

            if lyginimas:
                Graphtitle = pavadinimai[0] + ' ir ' + pavadinimai[1]
            else:
                Graphtitle = pavadinimai[0] + ' ir ' + pavadinimai[1] + ': ' + sal

            ax.plot(duomenys.index.values, duomenys[pavadinimai[0]] , label = pavadinimai[0] + ' ' + sal) #color eina prieš label color = 'blue
            ax.set(xlabel = "Metai", ylabel = pavadinimai[0],  title = Graphtitle)
            
            if len(axis) > 1:
                if sal == salis[0] or lyginimas == False:
                    ax2 = ax.twinx()
                ax2.plot(duomenys.index.values, duomenys[pavadinimai[1]] , color = spalvos[-1], label = pavadinimai[1] + ' ' + sal)
                ax2.set_ylabel(pavadinimai[1])
            spalvos.pop()

        else:
            Graphtitle = pavadinimai[0] + ': ' + sal
            ax.plot(duomenys.index.values, duomenys[pavadinimaiChange[0]] , label = pavadinimaiChange[0] + ' ' + sal) #color eina prieš label color = 'blue
            ax.set(xlabel = "Metai", ylabel = pavadinimaiChange[0],  title = Graphtitle)
            if len(axis) > 1:
                Graphtitle = pavadinimai[0] + ' ir ' + pavadinimai[1]  + ': ' + sal
                ax.plot(duomenys.index.values, duomenys[pavadinimaiChange[1]] , label = pavadinimaiChange[1] + ' ' + sal) #color eina prieš label color = 'blue
                ax.set(xlabel = "Metai", ylabel = pavadinimaiChange[1],  title = Graphtitle)
            
        
        if lyginimas == False:
            Grafas.legend(loc="upper left", bbox_to_anchor=(0,1), bbox_transform=ax.transAxes)
            plt.savefig('Grafas.png', dpi = 400)
            await ctx.send(file=discord.File('Grafas.png'))


    if lyginimas == True:
        Grafas.legend(loc="upper left", bbox_to_anchor=(0,1), bbox_transform=ax.transAxes)
        plt.savefig('Grafas.png', dpi = 400)
        await ctx.send(file=discord.File('Grafas.png'))



@bot.command(name = 'excel') #excel iš wbgapi
async def excel(ctx, kas, *, args):
    
    if kas in ['salis', 'salys', 'šalys', 'šalis', 'country', 'countries']:
        axis, pavadinimai, years, salis, saliscode, pervadinimai, lyginimas, change, pavadinimaiChange = await sortArgs(ctx, args)
        
        if len(axis) == 0:   
            await ctx.send('Nėra rodiklio(-ių), prašau įrašykite rodiklį(-ius)')
            return

        if len(salis) == 0:
            await ctx.send('Nėra šalies(-ių), prašau įrašykite šalį(-is)')
            return
        
        if len(years) == 0:
            years = [date.today().year]

        #for sal, code in zip(salis, saliscode):
        
        file_path = os.path.join(os.path.dirname(__file__), 'Duomenys.xlsx')
        
        if os.path.exists(file_path):
            os.remove(file_path)

        kodai = []


        with pd.ExcelWriter('Duomenys.xlsx') as writer:

            for kodas, sal in zip(saliscode, salis):
                kodai.append(kodas['alpha3'])
                sal =sal.replace('_', ' ')

                try:
                    duomenys = wb.data.DataFrame(axis, kodas['alpha3'], range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
                    duomenys = pd.DataFrame(duomenys)
                except: 
                    years = [2000, date.today().year]
                    duomenys = wb.data.DataFrame(axis, kodas['alpha3'],  range(min(years), max(years)), numericTimeKeys = True, labels = True, columns = 'series')
                    duomenys = pd.DataFrame(duomenys)
                    await ctx.send('Neegzistuojantis metai. Rinksim duomenis nuo 2000 iki dabar')

                duomenys.rename(columns = pervadinimai, inplace = True)
        
                if change == True:
                    for i in range(len(pavadinimai)):
                        duomenys[pavadinimai[i]+' pokytis %'] = duomenys[pavadinimai[i]].pct_change(-1).mul(100)
            
                    try:  
                        duomenys.to_excel(writer, sheet_name=f'{sal}')
                    except:
                        await ctx.send(f'Kažkodėl negalime įdėti {sal} duomenų į excel failą (Galimai missing openpyxl library)')

        await ctx.send(file=discord.File('Duomenys.xlsx'))

    elif kas in ['kompanijos', 'kompanija', 'company', 'companies', 'ticker', 'tickers']:
        
        tickeriai, pavadinimai, years, ratios, tinkama = await sortCompArgs(ctx, args)

        for ticker in tickeriai:

            file_path = os.path.join(os.path.dirname(__file__), 'CompanyInfoDump.xlsx')
        
            if os.path.exists(file_path):
                os.remove(file_path)

            save_all_data_to_excel(ticker)

            await ctx.send(file=discord.File('CompanyInfoDump.xlsx'))

    else:        
        await ctx.send('Nepažįstamas excel tipo argumentas. Naudokite funkciją: /excel [salis/šalis/šalys/country/countries/kompanijos/kompanija/company/companies/ticker/tickers] [kita info]')





@bot.command(name = 'ratios') #kompanijos ratios spitina
async def ratios(ctx, *, msg):
         
    tickeriai, pavadinimai, years, ratios, tinkama = await sortCompArgs(ctx, msg)


    if tinkama == False:
        return

    if len(tickeriai) == 1:

        embed = discord.Embed(title="Kompanijos info:", colour=discord.Colour.default())

        query = f'logo company:{pavadinimai[0]} ticker:{tickeriai[0]}'
        paieska = f"https://www.google.com/search?q={query}&tbm=isch"
        foto = requests.get(paieska)

        soup = BeautifulSoup(foto.text, "html.parser")

        img_tag = soup.find("img", {"class": "DS1iW"})

        if img_tag is not None:
            img_link = img_tag.get("src")
            #print(img_link)
            embed.set_thumbnail(url = img_link)
        else:
            await ctx.send('Nerastas logotipas') 

        #print(soup.prettify())
    else: 
        embed = discord.Embed(title="Kompanijų info:", colour=discord.Colour.default())


        #========================Vytis========================#

        #========================Gvidas========================#
    fields = 0

    for ticker, pavadinimas in zip(tickeriai, pavadinimai):
        akcija = yf.Ticker(ticker)
        

        try:
            fast = akcija.fast_info
            info = akcija.info  # čia atsiranda EPS, dividendai, PB ir pan.
            income = akcija.income_stmt
            balance = akcija.balance_sheet
            cashflow = akcija.cashflow
            history = akcija.history_metadata
        except:
            await ctx.send(f'Nepavyko gauti duomenų apie {ticker} kompaniją')
            continue


        def safe_get(df, candidates):
            """Grąžina pirmą rastą eilutę pagal pateiktus raktus."""
            for label in candidates:
                if label in df.index:
                    series = df.loc[label]
                    return series.iloc[0] if not series.empty else None
            return None


        def safe_div(numerator, denominator):
            if numerator is None or denominator in (0, None):
                return None
            return numerator / denominator


        pavadinimas = history.get('shortName')
        industry = info.get('industry')

        kaina = fast.get("lastPrice")
        market_cap = fast.get("marketCap")
        shares_outstanding = info.get("sharesOutstanding")
        eps = info.get("trailingEps")

        pajamos = safe_get(income, ["Total Revenue", "TotalRevenue"])
        grynasis_pelnas = safe_get(income, ["Net Income", "NetIncome"])
        turtas = safe_get(balance, ["Total Assets"])
        nuosavas_kapitalas = safe_get(balance, ["Stockholders Equity", "Common Stock Equity"])
        skolos = safe_get(balance, ["Total Liabilities Net Minority Interest", "Total Debt"])
        trumpalaikes_skolos = safe_get(balance, ["Current Liabilities"])
        trumpalaikis_turtas = safe_get(balance, ["Current Assets"])
        grynieji = safe_get(balance, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
        try:
            ev = market_cap + skolos - grynieji
        except:
            ev = None
        
        
        ebitda = safe_get(income, ['EBITDA'])
        ev_to_ebitda = safe_div(ev, ebitda)
        volume = info.get('volume')
        forwardPE = info.get('forwardPE')



        operacinis_cf = safe_get(cashflow, ["Total Cash From Operating Activities"])
        laisvas_cf = safe_get(cashflow, ["Free Cash Flow"])


        # Santykiai
        pe = safe_div(kaina, eps)
        roe = safe_div(grynasis_pelnas, nuosavas_kapitalas)
        roa = safe_div(grynasis_pelnas, turtas)
        fcf_marza = safe_div(laisvas_cf, pajamos)
        debt_to_equity = safe_div(skolos, nuosavas_kapitalas)
        debt_to_ebitda = safe_div(skolos, ebitda)
        current_ratio = safe_div(trumpalaikis_turtas, trumpalaikes_skolos)

        dividend_yield = info.get("dividendYield")  # jau procentais (pvz. 0.005 = 0.5 %)
        price_to_book = info.get("priceToBook")
        beta = info.get("beta")

        try:
            roe = str(round(roe,3))
        except:
            roe = roe

        try:
            roa = str(round(roa,3))
        except:
            roa = roa

        try:
            fcf_marza = str(round(fcf_marza, 3))
        except:
            fcf_marza = fcf_marza




        duomenys = {
            "ticker": ticker,
            "industry": industry, 
            "kaina": kaina,
            "kapitalizacija": market_cap,
            "ev" : ev,
            "akcijų skaičius": shares_outstanding,
            "volume": volume,
            "pajamos": pajamos,
            "grynasis pelnas": grynasis_pelnas,
            "ebitda": ebitda,
            "turtas": turtas,
            "nuosavas kapitalas": nuosavas_kapitalas,
            "visos skolos": skolos,
            "trumpalaikis turtas": trumpalaikis_turtas,
            "trumpalaikės skolos": trumpalaikes_skolos,
            "grynieji": grynieji,
            "operacinis cf": operacinis_cf,
            "laisvas cf": laisvas_cf,
            "eps": eps,
            "p/e": pe,
            "ev/ebitda": ev_to_ebitda,
            "forward p/e": forwardPE, 
            "roe": str(roe) + ' %',
            "roa": str(roa) + ' %',
            "fcf marža": str(fcf_marza) + ' %',
            "debt/equity": debt_to_equity,
            "debt/ebitda": debt_to_ebitda,
            "current ratio": current_ratio,
            "dividend yield": str(dividend_yield) + ' %',
            "price/book": price_to_book,
            "beta": beta,
        }

        if len(tickeriai) == 1:
            query = f'logo company:{pavadinimas} ticker:{tickeriai[0]}'
            paieska = f"https://www.google.com/search?q={query}&tbm=isch"
            foto = requests.get(paieska)

            soup = BeautifulSoup(foto.text, "html.parser")

            img_tag = soup.find("img", {"class": "DS1iW"})

            if img_tag is not None:
                img_link = img_tag.get("src")
                #print(img_link)
                embed.set_thumbnail(url = img_link)
            else:
                await ctx.send('Nerastas logotipas') 

        if pavadinimas == ticker:
            Ftitle = ticker
        else:
            Ftitle = f'{pavadinimas} ({ticker})'

        Vinfo = ''


        if ratios == []:
            for key, value in duomenys.items():
                key = key.capitalize()
                try:
                    value = round(value, 2)
                except:
                    value = value

                if value is None or value == 'None %':
                    continue

                try:
                    if value >= 1000:
                        Vinfo = Vinfo + f'{key}: {numerize.numerize(int(value), 3)}\n'
                    else:
                        Vinfo = Vinfo + f'{key}: {value}\n'
                except:
                    Vinfo = Vinfo + f'{key}: {value}\n'
        else:
            for ratio in ratios:
                try:
                    pav = ratio.capitalize()

                    try:
                        duomenys[ratio] = round(duomenys[ratio], 2)
                    except:
                        duomenys[ratio] = duomenys[ratio]

                    try:
                        if duomenys[ratio] >= 1000:
                            Vinfo = Vinfo + f'{pav}: {numerize.numerize(int(duomenys[ratio]), 3)}\n'
                        else:
                            Vinfo = Vinfo + f'{pav}: {duomenys[ratio]}\n'
                    except:
                        Vinfo = Vinfo + f'{pav}: {duomenys[ratio]}\n'
                except:
                    await ctx.send(f'Neatpažintas santykis: {ratio}')

        embed.add_field(name = Ftitle, value = Vinfo)
        fields = fields+1
        


    if fields != 0:
        await ctx.send(embed=embed)
    else:
        return





    #========================Gvidas========================#






# Run the bot
bot.run('MTQzNTcxNjMyNjYzMDEwMTA2Mw.GtqeBX.gjP7qClE17dxSUOqyn-EkViHUMmbnHcSe2rsPM', log_handler=handler, log_level=logging.DEBUG)