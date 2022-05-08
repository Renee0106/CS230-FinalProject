"""
Class: CS 230
Name: Renee Shi
Final project to play with Cambridge Property Database
"""
import streamlit as st
import pydeck as pdk
import pandas as pd
import matplotlib.pyplot as plt


DEBUG = False
csv_file = "Cambridge_Property_Database_FY2022_8000_sample.csv"
st_title = "Cambridge Property"


def read_data_from_csv(csvfile):
    df = pd.read_csv(csvfile)
    return df


def get_data_bedroom(df, bedrooms=[1]):
    df = df[df["Interior_Bedrooms"].isin(bedrooms)]
    return df


def get_data_saleyear(df, saleyear):
    df = df[df["SaleYear"].isin(saleyear) & (df["SalePrice"] > 1000)]
    return df


def main():
    df = read_data_from_csv(csv_file)
    st.title(st_title)
    if DEBUG:
        print(f"{df.info = }")
        print(f"{df.shape = }")
    st.write("")

    # Question #1
    bedrooms = [1, 2, 3, 4]
    df_summary = get_data_bedroom(df, bedrooms)
    df_summary["SaleYear"] = pd.to_datetime(df_summary['SaleDate']).dt.year
    picked_sale_year = [2018, 2019, 2020, 2021, 2022]
    df_summary = get_data_saleyear(df_summary, picked_sale_year)
    columns_show = ["Interior_Bedrooms", "SalePrice", "SaleDate", "SaleYear"]
    df_summary = df_summary[columns_show]
    df_summary["Interior_Bedrooms"] = df_summary["Interior_Bedrooms"].astype('Int64')

    df_summary = df_summary.groupby(['Interior_Bedrooms', 'SaleYear'])\
        .agg(
                Max_SalePrice=('SalePrice', "max"),
                Min_SalePrice=('SalePrice', "min"),
                Avg_SalePrice=('SalePrice', "mean"),
                Count=('SalePrice', "count")
            )

    df_summary["Max_SalePrice"] = df_summary["Max_SalePrice"].map('{:,.0f}'.format)
    df_summary["Min_SalePrice"] = df_summary["Min_SalePrice"].map('{:,.0f}'.format)
    df_summary["Avg_SalePrice"] = df_summary["Avg_SalePrice"].map('{:,.0f}'.format)
    df_summary.rename(columns={'Max_SalePrice': 'Max', 'Min_SalePrice': 'Min', 'Avg_SalePrice': 'Avg'}, inplace=True)

    if DEBUG:
        print(f"{df_summary.head()}")

    st.write(f"1. The SalePrice summary for these years {picked_sale_year}: ")
    st.dataframe(df_summary, height=500)

    st.write("")
    st.write("")
    st.markdown("""---""")

    # Question #2
    st.write(f"2. What types of houses the buyers could purchase? ")
    low_number = 100000
    step_number = 10000
    high_number = 9000000 + step_number
    initial_low = 100000
    initial_high = 5000000

    low_price, high_price = st.select_slider('Select the price range?', range(low_number, high_number, step_number),
                                             [initial_low, initial_high])
    st.write(f"The price range is from {low_price} to {high_price}")

    col_room_number, col_neighborhoods = st.columns([1, 2])
    with col_room_number:
        room_number = st.selectbox("How many bedrooms you want?", bedrooms)
        if DEBUG:
            st.write(f"You chose {room_number} bedrooms.")
    with col_neighborhoods:
        neighborhoods = df["TaxDistrict"].unique()
        neighborhoods_selected = st.multiselect("What are the neighborhoods you would like?",
                                                neighborhoods, neighborhoods[0])
        if DEBUG:
            st.write(f"You chose  {neighborhoods_selected} neighborhoods")

    columns_show = ['Address', 'Unit', 'SalePrice', 'SaleDate',
                    'Interior_TotalRooms', 'Interior_Bedrooms', 'Interior_FullBaths',
                    'Parking_Garage', 'PropertyTaxAmount', 'Latitude', 'Longitude', 'TaxDistrict']
    df_search = df[(df['SalePrice'] >= low_price) & (df['SalePrice'] <= high_price)
                   & (df['Interior_Bedrooms'] == room_number)
                   & (df['TaxDistrict'].isin(neighborhoods_selected))][columns_show]
    df_search["SalePrice"] = df_search["SalePrice"].fillna(0).map('{:,.0f}'.format)
    df_search["PropertyTaxAmount"] = df_search["PropertyTaxAmount"].fillna(0).map('{:,.0f}'.format)
    df_search["Interior_TotalRooms"] = df_search["Interior_TotalRooms"].fillna(0).astype('Int64')
    df_search["Interior_Bedrooms"] = df_search["Interior_Bedrooms"].fillna(0).astype('Int64')
    df_search["Interior_FullBaths"] = df_search["Interior_FullBaths"].fillna(0).astype('Int64')
    df_search["Parking_Garage"] = df_search["Parking_Garage"].fillna(0).astype('Int64')
    df_search["Unit"] = df_search["Unit"].fillna(0).astype("string")
    df_search["Latitude"] = df_search["Latitude"].fillna(method="backfill")
    df_search["Longitude"] = df_search["Longitude"].fillna(method="backfill")
    df_search.rename(columns={'Interior_TotalRooms': 'TotalRooms', 'Interior_Bedrooms': 'Bedrooms'}, inplace=True)
    df_search.rename(columns={'Interior_FullBaths': 'FullBaths', 'Parking_Garage': 'Garage'}, inplace=True)

    df_search = df_search.sort_values(by=['TaxDistrict', 'SalePrice'])

    st.dataframe(df_search)

    layer = pdk.Layer(type='ScatterplotLayer',
                      data=df_search,
                      get_position='[Longitude, Latitude]',
                      auto_highlight=True,
                      get_radius=150,
                      get_color=[200, 0, 200],
                      pickable=True
                      )

    view_state = pdk.ViewState(
        latitude=df_search["Latitude"].mean(),
        longitude=df_search["Longitude"].mean(),
        zoom=11,
        pitch=0)

    tool_tip = {"html": "Property Info:<br/> <b>{Address}</b> <br/> <b>{SalePrice}</b>",
                "style": {"backgroundColor": "orange", "color": "white"}
                }

    boston_map = pdk.Deck(
        map_style='mapbox://styles/mapbox/outdoors-v11',
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tool_tip
    )

    st.pydeck_chart(boston_map)

    st.write("")
    st.write("")
    st.markdown("""---""")

    # Question #3
    st.write(f"3. What are the top 10 house value increasing in each house categories? ")

    propertyclass_list = []
    condo_list = []
    single_family_list = []
    multi_family_list = []
    for pc in df.PropertyClass:
        if pc.lower().strip() not in propertyclass_list:
            propertyclass_list.append(pc.lower().strip())
            if "apt" in pc.lower() and pc not in condo_list:
                condo_list.append(pc)
            if "condo" in pc.lower() and pc not in condo_list:
                condo_list.append(pc)
            if "cndo" in pc.lower() and pc not in condo_list:
                condo_list.append(pc)
            if "sngl" in pc.lower() and pc not in single_family_list:
                single_family_list.append(pc)
            if "single" in pc.lower() and pc not in single_family_list:
                single_family_list.append(pc)
            if "multiple" in pc.lower() and pc not in multi_family_list:
                multi_family_list.append(pc)
            if "two-fam" in pc.lower() and pc not in multi_family_list:
                multi_family_list.append(pc)
            if "multiuse-res" in pc.lower() and pc not in multi_family_list:
                multi_family_list.append(pc)
            if "three-fm-res" in pc.lower() and pc not in multi_family_list:
                multi_family_list.append(pc)
            if "mult-res" in pc.lower() and pc not in multi_family_list:
                multi_family_list.append(pc)

    df["IncreasedValue"] = 0
    df["PropertyClass2"] = "Commercial"
    df.loc[df['PropertyClass'].isin(condo_list), 'PropertyClass2'] = 'Condo'
    df.loc[df['PropertyClass'].isin(single_family_list), 'PropertyClass2'] = 'Single Family'
    df.loc[df['PropertyClass'].isin(multi_family_list), 'PropertyClass2'] = 'Multiple Family'

    property_type = ['Condo', 'Single Family', 'Multiple Family']
    property_class = st.selectbox('Select one type of property class', property_type)

    columns_show = ["Address", "Unit", "AssessedValue", "PreviousAssessedValue", "IncreasedValue", "PropertyClass2"]
    df_increase = df[(df['PropertyClass2'] == property_class) & (df['PreviousAssessedValue'] > 0)][columns_show]
    df_increase.drop_duplicates(inplace=True)
    df_increase["IncreasedValue"] = df_increase["AssessedValue"] - df_increase["PreviousAssessedValue"]
    df_increase["IncreasedValue"] = df_increase["IncreasedValue"].fillna(0).astype('Float64')
    df_increase = df_increase.nlargest(n=10, columns=['IncreasedValue'])
    df_increase["AssessedValue"] = df_increase["AssessedValue"].fillna(0).map('{:,.0f}'.format)
    df_increase["PreviousAssessedValue"] = df_increase["PreviousAssessedValue"].fillna(0).map('{:,.0f}'.format)
    df_increase["IncreasedValue"] = df_increase["IncreasedValue"].fillna(0).map('{:,.0f}'.format)
    if DEBUG:
        print(f"{df_increase = }")
    st.write(df_increase)

    st.write("")
    st.write("")
    st.markdown("""---""")

    # Question #4
    st.write(f"4. What are the most out-of-cambridge buyers zipcodes? ")
    cambridge_zipcode = ['02138', '02139', '02140', '02141', '02142']
    columns_show = ["Address", "Unit", "Owner_Zip", "PropertyClass2"]
    property_class = st.multiselect('Select one type of property class', property_type, property_type[:])
    df3 = df[(df['PropertyClass2'].isin(property_class))][columns_show]
    df3.drop_duplicates(inplace=True)
    df3['Owner_Zip'] = df3['Owner_Zip'].str.split(pat='-').str[0]
    df3 = df3[~df3['Owner_Zip'].isin(cambridge_zipcode)][columns_show]
    df_owner = df3.groupby(['Owner_Zip']).agg(Count=('Owner_Zip', "count"))
    df_owner = df_owner.nlargest(n=10, columns=['Count'])

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        fig1, ax1 = plt.subplots()
        ax1.pie(df_owner.values.flatten(), labels=df_owner.index, autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig1)
    with col_table:
        st.dataframe(df_owner)

    if DEBUG:
        print(f"{df_owner.head(10)}")


if __name__ == "__main__":
    main()
