from config import *

if __name__ == '__main__':

    # Logging Setting
    logging.basicConfig(filename="file.log",
                        level=logging.INFO,
                        format='%(levelname)s   %(asctime)s   %(message)s')

    logging.info("All setting of the logging is done")

    # Read Credentials
    config = ConfigParser()
    path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(path)
    zip_file = config.get('credentials', 'zip_file_name')
    zip_dataset = config.get('credentials', 'zip_dataset_name')
    receiver_email = config.get('credentials', 'receiver_email')
    sender_email = config.get('credentials', 'sender_email')
    email_password = config.get('credentials', 'email_password')
    pio.renderers.default = 'browser'
    geojson_url = config.get('credentials', 'geojson_url')
    sender = config.get('credentials', 'sender')
    password = config.get('credentials', 'password')
    receiver = config.get('credentials', 'receiver')
    logging.info("Credentials have read successfully")

    # Extract dataset
    path = os.getcwd()
    extract_zip(path, zip_file)
    extract_zip(path, zip_dataset)
    logging.info("Zipfile is extracted")

    # Read the Data
    files = os.listdir()
    for i in files:
        if "populationbycountry19802010millions.csv" in i:
            dff = pd.read_csv(i)
            logging.info("Data has been read successfully")
            break

    # Data Preprocessing
    # Drop None Values
    dff.dropna(inplace=True)

    # Change Unnamed column to Country
    dff.rename(columns={'Unnamed: 0': 'Country'}, inplace=True)

    # Capitalize Country Column
    dff['Country'] = dff['Country'].apply(lambda x: x.capitalize())

    # Keep just numbers of df
    dff["only_number"] = dff.apply(lambda row: check_is_number(row), axis=1)
    dff = dff[dff["only_number"] == True]

    # Convert all numeric columns with object type to float
    df = dff.copy()
    df.loc[:, df.columns != "Country"] = df.loc[:, df.columns != "Country"].apply(pd.to_numeric)

    # Drop only_number column
    df.drop("only_number", axis=1, inplace=True)
    logging.info("Data preprocessing is done")

    # Create Country Code
    cc = coco.CountryConverter()
    df['Country_code'] = df['Country'].apply(lambda x: cc.convert(x))
    df = df[df["Country_code"] != "not found"]

    # First Question (Most populated country or area in 2000)
    r1 = df[df['2000'] == df['2000'].max()]['Country']

    # Second Question (The Highest increase of population is related to which country from 1980 to 2010)
    df['increase'] = df['2010'] - df['1980']

    r2 = df[df['increase'] == df['increase'].max()]['Country']
    # df.sort_values(by=['increase'], ascending=False)['Country'][0:5] First five highest increase

    # Third Question (Average population of Italy during 1980 till 2010)
    df['mean'] = df.mean(axis=1)
    r3 = df[df['Country'] == "Italy"]['mean']

    # Write all answers in a text file
    results = open("results.txt", "w")  # write mode
    results.write(f"Answer 1 \nThe most populated country or area in 2000 is {r1.to_list()[0]} \n \n")
    results.write(f"Answer 2 \nHighest increase of population from 1980 to 2010 is reloated to {r2.to_list()[0]} \n \n")
    results.write(f"Answer 3 \nAverage population of Italy during 1980 till 2010 is {str(r3.to_list()[0])[:5]} \n \n")
    results.close()
    logging.info("All answers of first 3 questions have been written in a text file")

    # Fourth Question (Picture of Heatmap of population by country 2010 with legend)
    map_data = df[df.columns[1:]]
    # Download countries geojson file
    if os.path.exists('countries.geojson'):
        logging.warning("The countries.geojson file exist in the folder")
        pass
    else:
        download_geojson(geojson_url)
    # Load countries geojson file
    with open('countries.geojson') as f:
        geojson = geojson.load(f)
    M = folium.Map(location=[0, 0], zoom_start=2)
    folium.Choropleth(
        geo_data=geojson,
        data=map_data,
        columns=['Country_code', '2010'],
        key_on='feature.id',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Population of countries at 2010"
    ).add_to(M)

    M.save("Folium_2010.html")

    fig = px.choropleth(
        df,
        locations="Country_code",
        geojson=geojson,
        color="2010",
        hover_name="Country_code",
        hover_data=["2010"],
        title="Population of countries at 2010"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.write_html("Plotly2010.html")

    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world = world.rename(columns={"iso_a3": "Country_code"})
    world = world.drop(['pop_est', 'continent', 'name', 'gdp_md_est'], axis=1)
    geo_df = world.merge(df, on='Country_code', how='inner')
    geo_df = geo_df.dropna()
    index_not_number = []
    for i in range(len(geo_df['2010'])):
        try:
            float(geo_df['2010'].iloc[i])
        except:
            index_not_number.append(i)
    geo_df = geo_df.drop(geo_df.index[index_not_number])
    geo_df.loc[:, geo_df.columns == "2010"] = geo_df.loc[:, geo_df.columns == "2010"].apply(pd.to_numeric)
    geo_df.plot(column='2010', figsize=(36, 10), legend=True).figure.savefig(
        'Plot_Bar_Legend.pdf')
    geo_df.plot(column='2010', figsize=(36, 10), legend=True, cmap='OrRd', scheme='quantiles').figure.savefig(
        'Plot_Scatter_Legend.pdf')
    logging.info("The plots of the question 4 have saved in different formats")

    # Fifth Question (Heatmap with time which shows the population changes)
    for year in range(1980, 2011):
        fig, ax = plt.subplots(figsize=(18, 10))
        plt.text(-190, -10, "Population of the World", fontsize=22)
        plt.text(-165, -38, f"{year}", fontsize=52)
        geo_df.plot(column=f'{year}', ax=ax, legend=True, cmap='OrRd', scheme='quantiles').figure.savefig(f'{year}.jpg')

    images = []
    files = os.listdir()

    for filename in files:
        if ".jpg" in filename:
            images.append(imageio.imread(filename))
            os.remove(filename)

    imageio.mimsave('Population.gif', images, duration=1)
    logging.info("All the images of the population are merged in a single gif file")

    # Last Step Sending Results to the Email
    result_list = ["results.txt", "Folium_2010.html", "Plotly2010.html", "Plot_Bar_Legend.pdf", "Plot_Scatter_Legend.pdf", "Population.gif", "file.log"]

    # Make a folder which name is Results to put all the results inside that
    if os.path.exists("Results"):
        pass
    else:
        os.mkdir("Results")
    destination = path + os.sep + "Results"
    logging.info("Results directory is created")

    # Move all the results in Results folder and zip the folder
    for item in result_list:
        source = path + os.sep + item
        shutil.copy(source, destination)

    shutil.make_archive("Results", "zip", destination)
    logging.info("All files are zipped and move to the results directory")

    delete_list = ["results.txt", "Folium_2010.html", "Plotly2010.html", "Plot_Bar_Legend.pdf",
                   "Plot_Scatter_Legend.pdf", "Population.gif", "countries.geojson", "populationbycountry19802010millions.csv"]
    for item in delete_list:
        os.remove(path + os.sep + item)
    logging.info("All extra files are deleted from the directory")

    # Send the Results.zip file to the Destination Email
    Subject = 'Python Task 1'
    msg = MIMEMultipart()
    # Prevent email goes to spam
    msg['From'] = formataddr((str(Header("AMIR", "utf-8")), sender))
    msg['To'] = receiver
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = Subject

    text = """\
    Hi,
    Please find the results file in the attachment
    have a great day
    Amir Sarrafzadeh Arasi"""

    part1 = MIMEText(text, "plain")

    msg.attach(part1)

    filename = "Results.zip"

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.ehlo()

    # Next, log in to the server
    server.login(sender, password)

    server.send_message(msg, msg.get("From"), msg.get("To"))
    logging.info("Email send with the attached file to the receivers")

