cd ~ || exit # Go to root, if failed kill the script
. onkyo/bin/activate # Launch the dedicated onkyo environment
cd  onkyo-api || exit # Go to the proper folder, if not present kill the script
python app.py # run the app
