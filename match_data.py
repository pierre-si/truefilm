# %%
import pandas as pd
from sqlalchemy import create_engine

# %% [markdown]
# - For each film, calculate the ratio of revenue to budget;  
# - Match each movie in the IMDB dataset with its corresponding Wikipedia page;  

# %% [markdown]
# # Load data

# %% [markdown]
# ## Movies

# %%
dtypes = {
    "budget": "float"
}
movies = pd.read_csv("movies_metadata.csv", usecols=[2, 8, 14, 15, 20])#, dtype=dtypes, on_bad_lines="skip")
# malformed rows (missing entries) may not have numeric values
movies[["budget", "revenue"]] = movies[["budget", "revenue"]].apply(pd.to_numeric, errors='coerce').dropna()
# movies = movies[movies.budget != 0]
movies["ratio"] = movies.revenue / movies.budget
# drop malformed rows (missing entries)
movies = movies.dropna(subset="title")
# drop duplicated entries
# same result with subset=["title", "release_date", "budget" ,"revenue"]
movies = movies.drop(index=movies[movies.duplicated(subset=["title", "release_date"])].index)

movies["processed_title"] = movies.title.str.lower()
movies.processed_title = movies.processed_title.str.replace(r'[^\w\s]+', '')
movies.processed_title = movies.processed_title.str.replace(' +', ' ')
# extract the year
movies["year"] = pd.to_datetime(movies.release_date).dt.year
# movies = movies.drop(columns="release_date")
movies

# %% [markdown]
# ## Wikipedia extract

# %%
urls = pd.read_csv("title-url.csv", names=["Title", "URL"])
urls = urls.dropna(subset="Title").reset_index(drop=True)
urls.Title = urls.Title.str.lower()
urls

# %% [markdown]
# ### Regex extract

# %%
urls = pd.concat([urls, urls["Title"].str.extract(r'\s\((?P<year>\d{4}\s)?(?P<country>.*)?(?P<film>film|tv series)\)$')], axis=1)
urls["Title"] = urls["Title"].str.replace(r'\s\((\d{4}\s)?(.*)?(film|tv series)\)$', '')
urls

# %% [markdown]
# ### Remove punctuation

# %%
urls.Title = urls.Title.str.replace(r'[^\w\s]+', '')
urls.Title = urls.Title.str.replace(' +', ' ')

# %% [markdown]
# # Merge
# Since we removed the "(film)" mentions from wikipedia titles, we now have multiple rows with the same title.  
# When doing a merge with movies_metadata on the left and wikipedia's entries on the right, we'll thus end up with the corresponding duplicate rows.

# %%
movies = pd.merge(movies, urls, how="left", left_on="processed_title", right_on="Title", suffixes=('', '_y'))
movies.shape

# %% [markdown]
# ## Remove duplicates
# We filter the duplicated rows and drop the ones which are not a film, or a film from a different year.

# %%
movies = movies.drop(index=movies[movies.duplicated(subset=["processed_title", "release_date"], keep=False) & (movies.film.isna())].index)

# %%
movies = movies.drop(index=movies[movies.duplicated(subset=["processed_title", "release_date"], keep=False) & (movies.year != movies.year_y.astype(float))].index)

# %% [markdown]
# # Postgres
# Load the top 1000 movies (with the highest ratio) into a Postgres database, including the following for each movie:  
# Title, budget, year, revenue, rating, ratio, production company, link to Wikipedia page, the Wikipedia abstract

# %%
# conn_url = 'postgresql+psycopg2://yourUserDBName:yourUserDBPassword@yourDBDockerContainerName/yourDBName'
#           ('postgresql://user:user_password@DB_service_name:5432/database_name'

# Default username: postgres
# Password: specified in docker-compose
# Service name: specified in docker-compose
# Default port: 5432
# Database name: specified in docker-compose

engine = create_engine('postgresql://postgres:example@db:5432/movies')

# %%
# Sort by ratio decreasing
with pd.option_context('mode.use_inf_as_na', True):
    movies = movies.sort_values("ratio", ascending=False)
movies

# %%
movies[["title", "budget", "year", "revenue", "ratio", "URL"]][:1000].to_sql("movies", engine)
