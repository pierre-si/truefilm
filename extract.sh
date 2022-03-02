# Wait for postgres container to start
sleep 5
# Database may already be populated
# Check if table movies exists
if [ "$(PGPASSWORD=example psql movies -h db -p 5432 -U postgres -tAc "SELECT EXISTS (
   SELECT FROM pg_tables
   WHERE  schemaname = 'public'
   AND    tablename  = 'movies'
);")" = 't' ]; then
    echo database already populated
    exit
else
    echo populating database
fi

# Download Wikipedia's dataset
# wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract.xml.gz
# gzip -d enwiki-latest-abstract.xml.gz

wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract27.xml.gz
gzip -d enwiki-latest-abstract27.xml.gz
mv enwiki-latest-abstract27.xml enwiki-latest-abstract.xml

# Extract titles and urls from Wikipedia's data
# <title> lines are always followed by <url> lines
grep -A1 --no-group-separator "</title>" enwiki-latest-abstract.xml |
# remove title tags
sed '1~2s/^.\{,18\}//;1~2s/.\{,8\}$//' |
# remove url tags
sed '2~2s/^.\{,5\}//;2~2s/.\{,6\}$//' |
# remove (film) substring
# sed 's/ (film)//g' |
# duplicate quotes that appear in titles
sed 's/"/""/g' |
# add leading and trailing quotes
sed 's/^/"/;s/$/"/' |
# concatenate title and url lines
sed '$!N;s/\n/,/' > title-url.csv

# Python script to match IMDB's movies to Wikipedia's data
# and upload it to the Postgres database. 
python3 match_data.py