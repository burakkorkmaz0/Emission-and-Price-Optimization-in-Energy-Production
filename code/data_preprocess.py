import pandas as pd
import os

# --- Corrected Relative Imports ---
try:
    from utils.sera_gazi import analyze_carbon_dioxide_emissions 
    from utils.yillik_fiyat import analyze_household_electricity_prices
    from utils.enerji_uretim import analyze_energy_production
    print("Analysis modules imported successfully using relative imports.")
except ImportError as e:
    print(f"Error: Could not import necessary analysis modules using relative imports: {e}")
    print("Please ensure 'sera_gazi.py', 'yillik_fiyat.py', and 'enerji_uretim.py'")
    print("are present in the SAME 'utils' directory as this script (data_preprocess.py) and have the correct function names.")
    print("Also ensure the 'utils' directory is a package (contains an __init__.py file).")
    print("If you are running this script directly, you might need to run it as a module from the parent directory, e.g., python -m utils.data_preprocess")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during module import: {e}")
    exit()
# --- End of Corrected Imports ---

def combine_all_data(country_codes=["DE", "FR"], start_year=2020, end_year=2023, remove_zero_production_sources=True):
    """
    Combines data from emissions, electricity prices, and energy production analyses
    for specified countries and year range into a single DataFrame.

    Args:
        country_codes (list): A list of geo codes for the countries (e.g., ["DE", "FR"]).
        start_year (int): The starting year for analysis.
        end_year (int): The ending year for analysis.
        remove_zero_production_sources (bool): If True, energy sources with zero production
                                               across all analyzed years for a country will be removed.

    Returns:
        pandas.DataFrame: A combined DataFrame ready for optimization, or None if an error occurs.
    """
    print(f"\nStarting combined data generation for countries {', '.join(country_codes)}, years {start_year}-{end_year}...")

    all_countries_data = [] # List to store DataFrames for each country

    country_code_to_name_map = {
        "DE": "Germany",
        "FR": "France"
        # Add other mappings if your analysis scripts use full names for other country codes
    }

    # Fetch multi-country data once
    print("\nFetching GHG emissions data (all target countries initially)...")
    df_emissions_pivot_multi_country = analyze_carbon_dioxide_emissions()
    
    print("\nFetching electricity price data (all target countries initially)...")
    df_prices_pivot_multi_country = analyze_household_electricity_prices()

    for country_code in country_codes:
        country_name = country_code_to_name_map.get(country_code.upper(), country_code.upper())
        print(f"\nProcessing data for {country_name} ({country_code})...")

        # Initialize DataFrame for the current country for this iteration
        years_index_current_country = pd.Index(range(start_year, end_year + 1), name='YEAR')
        current_country_combined_df = pd.DataFrame(index=years_index_current_country)


        # 1. Process Emissions Data for the current country
        df_emissions_processed_cc = pd.DataFrame(index=years_index_current_country) # Default empty
        if df_emissions_pivot_multi_country is not None and not df_emissions_pivot_multi_country.empty:
            TARGET_NACE_SECTOR_CONST = "Electricity, gas, steam and air conditioning supply" 
            try:
                if (country_name in df_emissions_pivot_multi_country.index.get_level_values('geo') and
                    TARGET_NACE_SECTOR_CONST in df_emissions_pivot_multi_country.index.get_level_values('nace_r2')):
                    df_country_sector_emissions = df_emissions_pivot_multi_country.loc[(country_name, TARGET_NACE_SECTOR_CONST)]
                    if not df_country_sector_emissions.empty:
                        df_emissions_transposed = df_country_sector_emissions.iloc[[0]].T 
                        df_emissions_transposed.index.name = 'YEAR'
                        unit_col_name = df_emissions_transposed.columns[0]
                        emissions_col_final_name = f"CO2_Emissions_{TARGET_NACE_SECTOR_CONST.split(',')[0].replace(' ','_')}_{str(unit_col_name).replace(' ','_')}"
                        df_emissions_temp_cc = df_emissions_transposed.rename(columns={unit_col_name: emissions_col_final_name})
                        df_emissions_temp_cc = df_emissions_temp_cc[
                            (df_emissions_temp_cc.index >= start_year) & (df_emissions_temp_cc.index <= end_year)]
                        if not df_emissions_temp_cc.empty:
                            df_emissions_processed_cc = df_emissions_temp_cc
                            print(f"  GHG emissions data processed for {country_name}.")
                else:
                    print(f"  Warning: Country '{country_name}' or sector '{TARGET_NACE_SECTOR_CONST}' not found in GHG emissions data for processing.")
            except KeyError:
                print(f"  Warning: KeyError accessing emissions data for country '{country_name}'.")
            except Exception as e:
                print(f"  An error occurred during emissions data processing for {country_name}: {e}")
        else:
            print(f"  Warning: GHG emissions master data is empty, skipping for {country_name}.")
        if df_emissions_processed_cc.empty:
             print(f"  Note: Emissions data for {country_name} ended up empty or was not processed.")


        # 2. Process Electricity Price Data for the current country
        df_prices_processed_cc = pd.DataFrame(index=years_index_current_country) # Default empty
        if df_prices_pivot_multi_country is not None and not df_prices_pivot_multi_country.empty:
            if country_name in df_prices_pivot_multi_country.columns:
                df_prices_temp_cc = df_prices_pivot_multi_country[[country_name]].copy()
                price_col_final_name = 'AvgHouseholdPrice_Euro_per_kWh'
                df_prices_temp_cc.columns = [price_col_final_name]
                df_prices_temp_cc = df_prices_temp_cc[
                    (df_prices_temp_cc.index >= start_year) & (df_prices_temp_cc.index <= end_year)]
                if not df_prices_temp_cc.empty:
                    df_prices_processed_cc = df_prices_temp_cc
                    print(f"  Electricity price data processed for {country_name}.")
            else:
                print(f"  Warning: Country '{country_name}' not found in electricity price data columns.")
        else:
            print(f"  Warning: Electricity prices master data is empty, skipping for {country_name}.")
        if df_prices_processed_cc.empty:
            print(f"  Note: Price data for {country_name} ended up empty or was not processed.")


        # 3. Get Energy Production Data for the current_country
        print(f"  Fetching energy production data for {country_code}...")
        summary_production_df_multi_idx, production_shares_pivot_multi_idx = analyze_energy_production(
            target_country_codes=[country_code], 
            start_year=start_year,
            end_year=end_year
        )
        
        df_production_summary_processed_cc = pd.DataFrame(index=years_index_current_country)
        if summary_production_df_multi_idx is not None and not summary_production_df_multi_idx.empty:
            if country_code in summary_production_df_multi_idx.index.get_level_values('geo'):
                df_prod_sum_temp_cc = summary_production_df_multi_idx.xs(country_code, level='geo')
                df_prod_sum_temp_cc.rename(columns={
                    'CalculatedTotalProduction_GWH': 'TotalProduction_GWh',
                    'TotalRenewableProduction_GWH': 'RenewableProduction_GWh',
                    'TotalRenewableShare (%)': 'RenewableShare_Percent'
                }, inplace=True)
                if not df_prod_sum_temp_cc.empty:
                     df_production_summary_processed_cc = df_prod_sum_temp_cc
                     print(f"  Energy production summary data processed for {country_code}.")
            else:
                 print(f"  Warning: {country_code} not found in energy production summary index.")
        else:
            print(f"  Warning: No energy production summary data returned for {country_code}.")
        if df_production_summary_processed_cc.empty:
            print(f"  Note: Production summary for {country_code} ended up empty or was not processed.")


        df_production_shares_processed_cc = pd.DataFrame(index=years_index_current_country)
        if production_shares_pivot_multi_idx is not None and not production_shares_pivot_multi_idx.empty:
            if country_code in production_shares_pivot_multi_idx.index.get_level_values('geo'):
                df_prod_shares_temp_cc = production_shares_pivot_multi_idx.xs(country_code, level='geo')
                if remove_zero_production_sources and not df_prod_shares_temp_cc.empty:
                    non_zero_sources = df_prod_shares_temp_cc.sum(axis=0) > 1e-6
                    df_prod_shares_temp_cc = df_prod_shares_temp_cc.loc[:, non_zero_sources]
                    print(f"    Removed energy sources with zero production for {country_code}.")
                if not df_prod_shares_temp_cc.empty:
                    df_prod_shares_temp_cc.columns = [
                        f"{str(col).replace(' (%)', '').replace(' ', '_').replace('-', '_').replace('.', '')}_Share_Percent" 
                        for col in df_prod_shares_temp_cc.columns
                    ]
                    df_production_shares_processed_cc = df_prod_shares_temp_cc
                    print(f"  Energy production shares data processed for {country_code}.")
            else:
                print(f"  Warning: {country_code} not found in energy production shares index.")

        else:
            print(f"  Warning: No energy production shares data returned for {country_code}.")
        if df_production_shares_processed_cc.empty:
            print(f"  Note: Production shares for {country_code} ended up empty or was not processed.")

        # Merge data for the current country
        if not df_emissions_processed_cc.empty:
            current_country_combined_df = current_country_combined_df.merge(df_emissions_processed_cc, on='YEAR', how='left')
        if not df_prices_processed_cc.empty:
            current_country_combined_df = current_country_combined_df.merge(df_prices_processed_cc, on='YEAR', how='left')
        if not df_production_summary_processed_cc.empty:
            current_country_combined_df = current_country_combined_df.merge(df_production_summary_processed_cc, on='YEAR', how='left')
        if not df_production_shares_processed_cc.empty:
            current_country_combined_df = current_country_combined_df.merge(df_production_shares_processed_cc, on='YEAR', how='left')
        
        if current_country_combined_df.shape[1] > 0: # Check if any columns were added
            current_country_combined_df['country_code'] = country_code # Add country identifier
            current_country_combined_df.reset_index(inplace=True) # Make YEAR a column for concat
            all_countries_data.append(current_country_combined_df)
            print(f"  Finished processing for {country_name}. Columns: {current_country_combined_df.shape[1]-1}") # -1 for country_code
        else:
            print(f"  Warning: No data columns were processed for {country_name}. Skipping this country in final output.")
    
    # Concatenate all country DataFrames
    if not all_countries_data:
        print("Error: No data processed for any country. Returning None.")
        return None

    final_combined_df = pd.concat(all_countries_data, ignore_index=True)
    # Set YEAR and country_code as multi-index if preferred, or keep them as columns
    final_combined_df.set_index(['country_code', 'YEAR'], inplace=True)
    
    print("\nOverall data combination complete.")
    return final_combined_df


if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 250) # Increased width for wider output
    pd.set_option('display.float_format', '{:.2f}'.format)

    try:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_for_dummies = os.path.dirname(current_script_dir) 
        datasets_for_dummies = os.path.join(project_root_for_dummies, 'datasets')
        os.makedirs(datasets_for_dummies, exist_ok=True)
        print(f"Ensuring dummy datasets folder exists at: {datasets_for_dummies}")

        dummy_prices_path = os.path.join(datasets_for_dummies, 'estat_nrg_pc_204$defaultview_filtered_en.csv')
        if not os.path.exists(dummy_prices_path):
            print(f"Creating dummy prices CSV for testing at: {dummy_prices_path}")
            dummy_p_data = {
                'geo': ['Germany', 'Germany', 'France', 'France', 'Germany', 'France', 'Germany', 'France'], 
                'TIME_PERIOD': ['2020-S1', '2020-S2', '2020-S1', '2020-S2', '2021-S1', '2021-S1', '2022-S1', '2022-S1'],
                'nrg_cons': ["Consumption from 2 500 kWh to 4 999 kWh - band DC"] * 8,
                'product': ["Electrical energy"] * 8, 'unit': ["Kilowatt-hour"] * 8,
                'tax': ["All taxes and levies included"] * 8, 'currency': ["Euro"] * 8,
                'OBS_VALUE': [0.30, 0.31, 0.18, 0.19, 0.32, 0.20, 0.35, 0.22]
            }
            pd.DataFrame(dummy_p_data).to_csv(dummy_prices_path, index=False)

        dummy_prod_path = os.path.join(datasets_for_dummies, 'estat_nrg_bal_peh.tsv')
        if not os.path.exists(dummy_prod_path):
            print(f"Creating dummy production TSV for testing at: {dummy_prod_path}")
            dummy_prod_content = (
                "freq,nrg_bal,siec,unit,geo\\TIME_PERIOD\t2022\t2021\t2020\n"
                "A,GEP,RA100,GWH,DE\t100\t90\t80\n"
                "A,GEP,FC_OTH_SOL_PHVPV,GWH,DE\t60\t55\t50\n"
                "A,GEP,NUC,GWH,DE\t30\t40\t50\n"
                "A,GEP,WIND,GWH,DE\t120\t110\t100\n" # Added Wind for DE
                "A,GEP,RA100,GWH,FR\t50\t45\t40\n"
                "A,GEP,FC_OTH_SOL_PHVPV,GWH,FR\t30\t25\t20\n"
                "A,GEP,NUC,GWH,FR\t210\t220\t230\n"
                "A,GEP,WIND,GWH,FR\t70\t60\t50\n"  # Added Wind for FR
            )
            with open(dummy_prod_path, 'w') as f: f.write(dummy_prod_content)
        
        dummy_siec_path = os.path.join(datasets_for_dummies, 'siec.csv')
        if not os.path.exists(dummy_siec_path):
            print(f"Creating dummy SIEC CSV for testing at: {dummy_siec_path}")
            dummy_siec_content = (
                "Notation,Label,Definition\n"
                "RA100,\"Hydro\",\"Hydro power\"\n"
                "FC_OTH_SOL_PHVPV,\"Photovoltaics\",\"Solar PV\"\n"
                "NUC,\"Nuclear\",\"Nuclear power\"\n"
                "WIND,\"Wind\",\"Wind power\"\n" 
            )
            with open(dummy_siec_path, 'w') as f: f.write(dummy_siec_content)

        dummy_emissions_path = os.path.join(datasets_for_dummies, 'estat_env_ac_ainah_r2$defaultview_filtered_en.csv')
        if not os.path.exists(dummy_emissions_path):
            print(f"Creating dummy emissions CSV for testing at: {dummy_emissions_path}")
            dummy_e_data = {
                'geo': ['Germany', 'Germany', 'France', 'France', 'Germany', 'France'], 
                'TIME_PERIOD': [2020, 2021, 2020, 2021, 2022, 2022],
                'nace_r2': ["Electricity, gas, steam and air conditioning supply"] * 6,
                'airpol': ["Carbon dioxide"] * 6, 
                'OBS_VALUE': [100.5, 110.2, 80.1, 85.3, 99.0, 78.0],
                'unit': ['Thousand tonnes'] * 6
            }
            pd.DataFrame(dummy_e_data).to_csv(dummy_emissions_path, index=False)
        print("Dummy data creation/check complete for imported modules.")
    except NameError: 
        print("Warning: __file__ not defined. Dummy data creation for sub-modules might fail.")
    except Exception as e:
        print(f"Error creating dummy files for sub-modules: {e}")

    final_combined_data_all = combine_all_data(
        country_codes=["DE", "FR"], # Now pass a list
        start_year=2020,
        end_year=2022, 
        remove_zero_production_sources=True 
    )

    if final_combined_data_all is not None and not final_combined_data_all.empty:
        print("\n--- FINAL COMBINED DATAFRAME (DE & FR) ---")
        print(final_combined_data_all)
    
        script_dir_main = os.path.dirname(os.path.abspath(__file__)) 
        project_root_main = os.path.dirname(script_dir_main) 
        output_data_folder_main = os.path.join(project_root_main, 'output_data')
        os.makedirs(output_data_folder_main, exist_ok=True)
        output_file_path_main = os.path.join(output_data_folder_main, f'combined_data_DE_FR_2020_2022.csv')
        try:
            final_combined_data_all.to_csv(output_file_path_main)
            print(f"\nCombined data for DE & FR saved to {output_file_path_main}")
        except Exception as e:
            print(f"Error saving combined data for DE & FR: {e}")
    else:
        print("\nFailed to generate combined data for DE & FR or the result was empty.")