import investpy

# CAC 40
df_cac = investpy.get_index_historical_data(index='CAC 40',
                                            country='france',
                                            from_date='01/01/2024',
                                            to_date='04/06/2025')

# Brent
df_brent = investpy.get_commodity_historical_data(commodity='Brent Oil',
                                                  from_date='01/01/2024',
                                                  to_date='04/06/2025')
