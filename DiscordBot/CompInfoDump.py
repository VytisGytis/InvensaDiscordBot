import yfinance as yf
import pandas as pd
import os
import openpyxl
from numerize import numerize
# Reikalinga openpyxl biblioteka Excel failų kūrimui
# Įdiegti: pip install openpyxl
# Reikalinga numerize biblioteka skaičių formatavimui
# Įdiegti: pip install numerize

# Galima naudoti ir crypto vietoj akcijos pvz: "BTC-USD", ETF ARBA FONDUS   
def get_all_ticker_data_as_dataframes(ticker_symbol):
    """
    Funkcija, kuri gauna visus ticker objektus ir konvertuoja juos į DataFrame.
    Series, dict, list, str, tuple konvertuojami į DataFrame.
    Visi kiti atributai, kurie jau yra DataFrame, paliekami kaip DataFrame.
    
    Args:
        ticker_symbol: akcijų simbolis (pvz., "AAPL", "MSFT", "BTC-USD")
    
    Returns:
        dict: žodynas su visais ticker duomenimis kaip DataFrame
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # Funkcija, kuri konvertuoja į DataFrame
    def to_dataframe(data, name=""):
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, pd.Series):
            return data.to_frame(name=name if name else "value")
        elif isinstance(data, dict):
            if len(data) == 0:
                return pd.DataFrame()
            # Jei dict su skaitinėmis reikšmėmis, konvertuojame į DataFrame
            try:
                return pd.DataFrame([data])
            except:
                # Jei negalima, bandome kaip stulpelių
                return pd.DataFrame(list(data.items()), columns=['key', 'value'])
        elif isinstance(data, list):
            if len(data) == 0:
                return pd.DataFrame()
            # Jei list su dict, konvertuojame į DataFrame
            if isinstance(data[0], dict):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame(data, columns=[name if name else "value"])
        elif isinstance(data, (str, int, float)):
            return pd.DataFrame([{name if name else "value": data}])
        elif isinstance(data, tuple):
            return pd.DataFrame(list(data), columns=[name if name else "value"])
        elif data is None:
            return pd.DataFrame()
        else:
            try:
                # Bandome konvertuoti kitus tipus
                return pd.DataFrame([data])
            except:
                return pd.DataFrame()
    
    # Gauname visus duomenis ir konvertuojame į DataFrame
    data_dict = {}
    
    # ========== ATRIBUTAI ==========
    
    # Dict atributai
    try:
        info = ticker.info
        if isinstance(info, dict):
            data_dict['info'] = pd.DataFrame([info])
        else:
            data_dict['info'] = to_dataframe(info, 'info')
    except:
        data_dict['info'] = pd.DataFrame()
    
    try:
        fast_info = ticker.fast_info
        if isinstance(fast_info, dict):
            data_dict['fast_info'] = pd.DataFrame([fast_info])
        else:
            data_dict['fast_info'] = to_dataframe(fast_info, 'fast_info')
    except:
        data_dict['fast_info'] = pd.DataFrame()
    
    try:
        analyst_price_targets = ticker.analyst_price_targets
        if isinstance(analyst_price_targets, dict):
            data_dict['analyst_price_targets'] = pd.DataFrame([analyst_price_targets])
        else:
            data_dict['analyst_price_targets'] = to_dataframe(analyst_price_targets, 'analyst_price_targets')
    except:
        data_dict['analyst_price_targets'] = pd.DataFrame()
    
    try:
        sec_filings = ticker.sec_filings
        if isinstance(sec_filings, dict):
            data_dict['sec_filings'] = pd.DataFrame([sec_filings])
        else:
            data_dict['sec_filings'] = to_dataframe(sec_filings, 'sec_filings')
    except:
        data_dict['sec_filings'] = pd.DataFrame()
    
    try:
        history_metadata = ticker.history_metadata
        if isinstance(history_metadata, dict):
            data_dict['history_metadata'] = pd.DataFrame([history_metadata])
        else:
            data_dict['history_metadata'] = to_dataframe(history_metadata, 'history_metadata')
    except:
        data_dict['history_metadata'] = pd.DataFrame()
    
    # List (dict) atributai
    try:
        news = ticker.news
        if isinstance(news, list):
            data_dict['news'] = pd.DataFrame(news) if news else pd.DataFrame()
        else:
            data_dict['news'] = to_dataframe(news, 'news')
    except:
        data_dict['news'] = pd.DataFrame()
    
    # Str atributai
    try:
        isin = ticker.isin
        data_dict['isin'] = pd.DataFrame([{'isin': isin}]) if isin else pd.DataFrame()
    except:
        data_dict['isin'] = pd.DataFrame()
    
    # Tuple atributai
    try:
        options = ticker.options
        if isinstance(options, tuple):
            data_dict['options'] = pd.DataFrame(list(options), columns=['option_date'])
        else:
            data_dict['options'] = to_dataframe(options, 'options')
    except:
        data_dict['options'] = pd.DataFrame()
    
    # Series atributai (konvertuojame į DataFrame)
    try:
        data_dict['dividends'] = to_dataframe(ticker.dividends, 'dividends')
    except:
        data_dict['dividends'] = pd.DataFrame()
    
    try:
        data_dict['splits'] = to_dataframe(ticker.splits, 'splits')
    except:
        data_dict['splits'] = pd.DataFrame()
    
    try:
        data_dict['capital_gains'] = to_dataframe(ticker.capital_gains, 'capital_gains')
    except:
        data_dict['capital_gains'] = pd.DataFrame()
    
    # DataFrame atributai (paliekame kaip DataFrame)
    try:
        data_dict['history'] = to_dataframe(ticker.history(), 'history')
    except:
        data_dict['history'] = pd.DataFrame()
    
    try:
        data_dict['actions'] = to_dataframe(ticker.actions, 'actions')
    except:
        data_dict['actions'] = pd.DataFrame()
    
    try:
        data_dict['financials'] = to_dataframe(ticker.financials, 'financials')
    except:
        data_dict['financials'] = pd.DataFrame()
    
    try:
        data_dict['quarterly_financials'] = to_dataframe(ticker.quarterly_financials, 'quarterly_financials')
    except:
        data_dict['quarterly_financials'] = pd.DataFrame()
    
    try:
        data_dict['balance_sheet'] = to_dataframe(ticker.balance_sheet, 'balance_sheet')
    except:
        data_dict['balance_sheet'] = pd.DataFrame()
    
    try:
        data_dict['quarterly_balance_sheet'] = to_dataframe(ticker.quarterly_balance_sheet, 'quarterly_balance_sheet')
    except:
        data_dict['quarterly_balance_sheet'] = pd.DataFrame()
    
    try:
        data_dict['cashflow'] = to_dataframe(ticker.cashflow, 'cashflow')
    except:
        data_dict['cashflow'] = pd.DataFrame()
    
    try:
        data_dict['quarterly_cashflow'] = to_dataframe(ticker.quarterly_cashflow, 'quarterly_cashflow')
    except:
        data_dict['quarterly_cashflow'] = pd.DataFrame()
    
    try:
        data_dict['income_stmt'] = to_dataframe(ticker.income_stmt, 'income_stmt')
    except:
        data_dict['income_stmt'] = pd.DataFrame()
    
    try:
        data_dict['quarterly_income_stmt'] = to_dataframe(ticker.quarterly_income_stmt, 'quarterly_income_stmt')
    except:
        data_dict['quarterly_income_stmt'] = pd.DataFrame()
    
    try:
        data_dict['quarterly_earnings'] = to_dataframe(ticker.quarterly_earnings, 'quarterly_earnings')
    except:
        data_dict['quarterly_earnings'] = pd.DataFrame()
    
    try:
        data_dict['calendar'] = to_dataframe(ticker.calendar, 'calendar')
    except:
        data_dict['calendar'] = pd.DataFrame()
    
    try:
        data_dict['earnings_dates'] = to_dataframe(ticker.earnings_dates, 'earnings_dates')
    except:
        data_dict['earnings_dates'] = pd.DataFrame()
    
    try:
        data_dict['major_holders'] = to_dataframe(ticker.major_holders, 'major_holders')
    except:
        data_dict['major_holders'] = pd.DataFrame()
    
    try:
        data_dict['institutional_holders'] = to_dataframe(ticker.institutional_holders, 'institutional_holders')
    except:
        data_dict['institutional_holders'] = pd.DataFrame()
    
    try:
        data_dict['mutualfund_holders'] = to_dataframe(ticker.mutualfund_holders, 'mutualfund_holders')
    except:
        data_dict['mutualfund_holders'] = pd.DataFrame()
    
    try:
        data_dict['sustainability'] = to_dataframe(ticker.sustainability, 'sustainability')
    except:
        data_dict['sustainability'] = pd.DataFrame()
    
    try:
        data_dict['recommendations'] = to_dataframe(ticker.recommendations, 'recommendations')
    except:
        data_dict['recommendations'] = pd.DataFrame()
    
    try:
        data_dict['recommendations_sum'] = to_dataframe(ticker.recommendations_sum, 'recommendations_sum')
    except:
        data_dict['recommendations_sum'] = pd.DataFrame()
    
    try:
        data_dict['upgrades_downgrades'] = to_dataframe(ticker.upgrades_downgrades, 'upgrades_downgrades')
    except:
        data_dict['upgrades_downgrades'] = pd.DataFrame()
    
    try:
        data_dict['earnings_estimate'] = to_dataframe(ticker.earnings_estimate, 'earnings_estimate')
    except:
        data_dict['earnings_estimate'] = pd.DataFrame()
    
    try:
        data_dict['revenue_estimate'] = to_dataframe(ticker.revenue_estimate, 'revenue_estimate')
    except:
        data_dict['revenue_estimate'] = pd.DataFrame()
    
    try:
        data_dict['growth_estimates'] = to_dataframe(ticker.growth_estimates, 'growth_estimates')
    except:
        data_dict['growth_estimates'] = pd.DataFrame()
    
    try:
        data_dict['insider_transactions'] = to_dataframe(ticker.insider_transactions, 'insider_transactions')
    except:
        data_dict['insider_transactions'] = pd.DataFrame()
    
    try:
        data_dict['insider_purchases'] = to_dataframe(ticker.insider_purchases, 'insider_purchases')
    except:
        data_dict['insider_purchases'] = pd.DataFrame()
    
    try:
        data_dict['insider_roster_holders'] = to_dataframe(ticker.insider_roster_holders, 'insider_roster_holders')
    except:
        data_dict['insider_roster_holders'] = pd.DataFrame()
    
    # Specialūs objektai (bandome konvertuoti)
    try:
        funds_data = ticker.funds_data
        # FundsData objektas - bandome gauti duomenis
        if hasattr(funds_data, '__dict__'):
            data_dict['funds_data'] = pd.DataFrame([funds_data.__dict__])
        else:
            data_dict['funds_data'] = pd.DataFrame()
    except:
        data_dict['funds_data'] = pd.DataFrame()
    
    # ========== METODAI ==========
    
    # Metodai, kurie grąžina Series (konvertuojame į DataFrame)
    try:
        data_dict['get_actions'] = to_dataframe(ticker.get_actions(), 'get_actions')
    except:
        data_dict['get_actions'] = pd.DataFrame()
    
    try:
        data_dict['get_dividends'] = to_dataframe(ticker.get_dividends(), 'get_dividends')
    except:
        data_dict['get_dividends'] = pd.DataFrame()
    
    try:
        data_dict['get_splits'] = to_dataframe(ticker.get_splits(), 'get_splits')
    except:
        data_dict['get_splits'] = pd.DataFrame()
    
    try:
        data_dict['get_capital_gains'] = to_dataframe(ticker.get_capital_gains(), 'get_capital_gains')
    except:
        data_dict['get_capital_gains'] = pd.DataFrame()
    
    # Metodai, kurie grąžina DataFrame arba dict
    try:
        balance_sheet = ticker.get_balance_sheet()
        data_dict['get_balance_sheet'] = to_dataframe(balance_sheet, 'get_balance_sheet')
    except:
        data_dict['get_balance_sheet'] = pd.DataFrame()
    
    try:
        cashflow = ticker.get_cashflow()
        data_dict['get_cashflow'] = to_dataframe(cashflow, 'get_cashflow')
    except:
        data_dict['get_cashflow'] = pd.DataFrame()
    
    try:
        financials = ticker.get_financials()
        data_dict['get_financials'] = to_dataframe(financials, 'get_financials')
    except:
        data_dict['get_financials'] = pd.DataFrame()
    
    try:
        income_stmt = ticker.get_income_stmt()
        data_dict['get_income_stmt'] = to_dataframe(income_stmt, 'get_income_stmt')
    except:
        data_dict['get_income_stmt'] = pd.DataFrame()
    
    try:
        earnings = ticker.get_earnings()
        data_dict['get_earnings'] = to_dataframe(earnings, 'get_earnings')
    except:
        data_dict['get_earnings'] = pd.DataFrame()
    
    # Metodai, kurie grąžina DataFrame
    try:
        data_dict['get_earnings_dates'] = to_dataframe(ticker.get_earnings_dates(), 'get_earnings_dates')
    except:
        data_dict['get_earnings_dates'] = pd.DataFrame()
    
    try:
        data_dict['get_recommendations'] = to_dataframe(ticker.get_recommendations(), 'get_recommendations')
    except:
        data_dict['get_recommendations'] = pd.DataFrame()
    
    try:
        data_dict['get_recommendations_sum'] = to_dataframe(ticker.get_recommendations_sum(), 'get_recommendations_sum')
    except:
        data_dict['get_recommendations_sum'] = pd.DataFrame()
    
    try:
        shares = ticker.get_shares()
        data_dict['get_shares'] = to_dataframe(shares, 'get_shares')
    except:
        data_dict['get_shares'] = pd.DataFrame()
    
    try:
        data_dict['get_shares_full'] = to_dataframe(ticker.get_shares_full(), 'get_shares_full')
    except:
        data_dict['get_shares_full'] = pd.DataFrame()
    
    # Metodai, kurie grąžina dict
    try:
        analyst_price_targets = ticker.get_analyst_price_targets()
        if isinstance(analyst_price_targets, dict):
            data_dict['get_analyst_price_targets'] = pd.DataFrame([analyst_price_targets])
        else:
            data_dict['get_analyst_price_targets'] = to_dataframe(analyst_price_targets, 'get_analyst_price_targets')
    except:
        data_dict['get_analyst_price_targets'] = pd.DataFrame()
    
    # Metodai, kurie grąžina str
    try:
        isin = ticker.get_isin()
        data_dict['get_isin'] = pd.DataFrame([{'isin': isin}]) if isin else pd.DataFrame()
    except:
        data_dict['get_isin'] = pd.DataFrame()
    
    # Metodai, kurie grąžina list (dict)
    try:
        news = ticker.get_news()
        if isinstance(news, list):
            data_dict['get_news'] = pd.DataFrame(news) if news else pd.DataFrame()
        else:
            data_dict['get_news'] = to_dataframe(news, 'get_news')
    except:
        data_dict['get_news'] = pd.DataFrame()
    
    # Specialūs metodai
    try:
        # option_chain() reikalauja datos parametro, todėl praleidžiame
        # Jei reikia, galima pridėti su konkrečia data
        pass
    except:
        pass
    
    return data_dict


def numerize_dataframe(df, apply_numerize=True):
    """
    Funkcija, kuri formatuoja DataFrame skaitines reikšmes su numerize biblioteka.
    Konvertuoja didelius skaičius į lengviau skaitomas formas (pvz., 1000000 -> 1M).
    
    Args:
        df: pandas DataFrame
        apply_numerize: ar taikyti numerize formatavimą (True/False)
    
    Returns:
        pandas.DataFrame: formatuotas DataFrame
    """
    if df.empty or not apply_numerize:
        return df
    
    # Sukuriame kopiją, kad nekeistume originalaus DataFrame
    df_formatted = df.copy()
    
    # Formatavimo funkcija
    def format_value(x):
        # Tikriname ar reikšmė yra None
        if x is None:
            return x
        
        # Tikriname ar yra NaN (float NaN patikrinimas: x != x yra True tik NaN atveju)
        if isinstance(x, float) and x != x:
            return x
        
        if isinstance(x, (int, float)):
            # Taikome numerize tik didesniems skaičiams (>= 1000)
            if abs(x) >= 1000:
                try:
                    return numerize(x)
                except:
                    # Jei numerize nepavyko, grąžiname originalų skaičių
                    return x
            else:
                return x
        elif isinstance(x, str):
            # Jei string, bandome konvertuoti į skaičių
            try:
                num = float(x)
                if abs(num) >= 1000:
                    return numerize(num)
                else:
                    return x
            except:
                return x
        else:
            return x
    
    # Taikome formatavimą visoms skaitinėms stulpeliams
    for col in df_formatted.columns:
        # Tikriname ar stulpelis yra skaitinis
        if df_formatted[col].dtype in ['int64', 'float64', 'int32', 'float32', 'Int64', 'Float64']:
            df_formatted[col] = df_formatted[col].apply(format_value)
        # Taip pat tikriname mixed types stulpelius
        elif df_formatted[col].dtype == 'object':
            # Bandome formatuoti, jei yra skaitinių reikšmių
            try:
                df_formatted[col] = df_formatted[col].apply(format_value)
            except:
                pass
    
    # Taip pat formatuojame indeksą, jei jis yra skaitinis
    if hasattr(df_formatted.index, 'dtype'):
        if df_formatted.index.dtype in ['int64', 'float64', 'int32', 'float32']:
            df_formatted.index = df_formatted.index.map(format_value)
    
    return df_formatted


def save_all_data_to_excel(ticker_symbol):
    """
    Funkcija, kuri gauna visus ticker duomenis ir išsaugo juos į Excel failą su atskirais lapais.
    Automatiškai taiko numerize formatavimą skaitinėms reikšmėms.
    
    Args:
        ticker_symbol: akcijų simbolis (pvz., "AAPL", "MSFT", "BTC-USD")
        excel_path: kelias iki Excel failo (pvz., "data.xlsx")
    """
    # Gauname visus duomenis
    ticker_data = get_all_ticker_data_as_dataframes(ticker_symbol)
    
    # Sukuriame ExcelWriter objektą
    with pd.ExcelWriter('CompanyInfoDump.xlsx') as writer:
        # Išsaugome kiekvieną DataFrame į atskirą lapą
        for sheet_name, df in ticker_data.items():
            # Excel lapo vardai negali būti ilgesni nei 31 simbolis
            # ir negali turėti specialių simbolių
            safe_sheet_name = sheet_name[:31].replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
            
            # Jei DataFrame nėra tuščias, formatuojame su numerize ir išsaugome
            if not df.empty:
                try:
                    # Visada taikome numerize formatavimą
                    df_formatted = numerize_dataframe(df, apply_numerize=True)
                    
                    df_formatted.to_excel(writer, sheet_name=safe_sheet_name, index=True)
                except Exception as e:
                    print(f"Klaida išsaugant {sheet_name}: {e}")
                    # Jei nepavyko, bandome be indekso
                    try:
                        df_formatted = numerize_dataframe(df, apply_numerize=True)
                        df_formatted.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    except:
                        print(f"Nepavyko išsaugoti {sheet_name}")
            else:
                # Net jei tuščias, sukuriame lapą su tuščiu DataFrame
                try:
                    pd.DataFrame().to_excel(writer, sheet_name=safe_sheet_name, index=False)
                except:
                    pass
    
    print(f"Išsaugota {len(ticker_data)} lapų")


# Pavyzdys naudojimo
if __name__ == "__main__":
    # Gauname visus ticker duomenis kaip DataFrame
    #ticker_data = get_all_ticker_data_as_dataframes("AAPL")
    
    # Išsaugome visus duomenis į Excel failą (automatiškai su numerize formatavimu)
    excel_path = r"C:\Users\gvida\OneDrive\Desktop\KTU_LAST_DANCE\KTU_LAST_DANCE\programavimas_test1.xlsx"
    save_all_data_to_excel("AAPL")
    
    #print("\nPrieinami duomenys:")
    #print(list(ticker_data.keys()))
    
    # Pavyzdys: formatuoti konkretų DataFrame su numerize
    # income_df = numerize_dataframe(ticker_data['income_stmt'], apply_numerize=True)
    # print("\nFormatuotas Income Statement:")
    # print(income_df)