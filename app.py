
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Movie Analytics Dashboard",
    page_icon="🎬",
    layout="wide"
)

SAMPLE_DATA = {
    "title": [
        "Inception", "Interstellar", "The Dark Knight",
        "Titanic", "Avatar", "The Matrix", "Gladiator",
        "Joker", "The Prestige", "Forrest Gump",
        "Coco", "Toy Story", "Up", "Finding Nemo",
        "Dune", "Oppenheimer", "The Lion King",
        "Parasite", "Whiplash", "The Shawshank Redemption"
    ],
    "year": [
        2010, 2014, 2008, 1997, 2009, 1999, 2000,
        2019, 2006, 1994, 2017, 1995, 2009, 2003,
        2021, 2023, 1994, 2019, 2014, 1994
    ],
    "rating": [
        8.8, 8.7, 9.0, 7.9, 7.9, 8.7, 8.5,
        8.4, 8.5, 8.8, 8.4, 8.3, 8.3, 8.2,
        8.0, 8.3, 8.5, 8.5, 8.5, 9.3
    ],
    "genres": [
        "Sci-Fi", "Sci-Fi", "Action", "Romance",
        "Sci-Fi", "Sci-Fi", "Action", "Drama",
        "Mystery", "Drama", "Animation", "Animation",
        "Animation", "Animation", "Sci-Fi", "Drama",
        "Animation", "Thriller", "Drama", "Drama"
    ]
}

st.title("🎬 Movie Data Analysis Dashboard")
st.write(
    "An interactive dashboard to explore movie ratings, "
    "release trends, and genres."
)

st.sidebar.header("Dashboard Controls")

uploaded_file = st.sidebar.file_uploader(
    "Upload your movie CSV (optional)",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    source = "Uploaded CSV"
else:
    df = pd.DataFrame(SAMPLE_DATA)
    source = "Sample dataset"

df.columns = [
    str(c).strip().lower().replace(" ", "_")
    for c in df.columns
]

aliases = {
    "title": ["movie_title", "name", "movie"],
    "year": ["release_year", "released"],
    "rating": ["imdb_rating", "score", "vote_average"],
    "genres": ["genre", "category"]
}

for standard, alternatives in aliases.items():
    if standard not in df.columns:
        for alt in alternatives:
            if alt in df.columns:
                df = df.rename(columns={alt: standard})
                break

for col, default in [
    ("title", "Unknown"),
    ("year", 0),
    ("rating", 0),
    ("genres", "Unknown")
]:
    if col not in df.columns:
        df[col] = default

df["title"] = df["title"].fillna("Unknown").astype(str)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["genres"] = df["genres"].fillna("Unknown").astype(str)

df = df.drop_duplicates()
df = df.dropna(subset=["year", "rating"])
df = df[(df["year"] > 0) & (df["rating"] > 0)]

if df.empty:
    st.error("No valid records found. Please upload a valid CSV.")
    st.stop()

df["year"] = df["year"].astype(int)

st.caption(f"Data source: {source} | Total valid records: {len(df)}")

st.sidebar.subheader("Filters")

min_year = int(df["year"].min())
max_year = int(df["year"].max())

if min_year < max_year:
    year_range = st.sidebar.slider(
        "Release year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
else:
    year_range = (min_year, max_year)

genre_options = sorted({
    genre.strip()
    for value in df["genres"]
    for genre in value.replace("|", ",").split(",")
    if genre.strip()
})

selected_genres = st.sidebar.multiselect(
    "Genre",
    options=genre_options,
    default=genre_options
)

search_text = st.sidebar.text_input("Search movie title")

filtered = df[
    df["year"].between(year_range[0], year_range[1])
].copy()

if selected_genres:
    filtered = filtered[
        filtered["genres"].apply(
            lambda value: any(
                g.strip().lower() in [
                    x.strip().lower()
                    for x in value.replace("|", ",").split(",")
                ]
                for g in selected_genres
            )
        )
    ]
else:
    filtered = filtered.iloc[0:0]

if search_text:
    filtered = filtered[
        filtered["title"].str.contains(
            search_text, case=False, na=False
        )
    ]

st.subheader("Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Movies", f"{len(filtered):,}")

if not filtered.empty:
    c2.metric("Average Rating", f"{filtered['rating'].mean():.2f}")
    c3.metric("Highest Rating", f"{filtered['rating'].max():.2f}")
    top_movie = filtered.loc[
        filtered["rating"].idxmax(), "title"
    ]
    c4.metric("Top-Rated Movie", top_movie[:25])
else:
    c2.metric("Average Rating", "N/A")
    c3.metric("Highest Rating", "N/A")
    c4.metric("Top-Rated Movie", "N/A")
    st.warning("No movies match your selected filters.")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Movies Released by Year")
    if not filtered.empty:
        yearly = (
            filtered.groupby("year")
            .size()
            .reset_index(name="movie_count")
        )
        fig = px.bar(
            yearly,
            x="year",
            y="movie_count",
            title="Number of Movies by Year",
            labels={
                "year": "Release Year",
                "movie_count": "Number of Movies"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Rating Distribution")
    if not filtered.empty:
        fig = px.histogram(
            filtered,
            x="rating",
            nbins=10,
            title="Distribution of Movie Ratings",
            labels={"rating": "Rating"}
        )
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Average Rating Trend")
    if not filtered.empty:
        trend = (
            filtered.groupby("year", as_index=False)["rating"]
            .mean()
            .sort_values("year")
        )
        fig = px.line(
            trend,
            x="year",
            y="rating",
            markers=True,
            title="Average Rating by Year",
            labels={
                "year": "Release Year",
                "rating": "Average Rating"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Movies by Genre")
    if not filtered.empty:
        genre_data = filtered.assign(
            genre=filtered["genres"].str.replace("|", ",", regex=False)
            .str.split(",")
        ).explode("genre")
        genre_data["genre"] = genre_data["genre"].str.strip()
        counts = genre_data["genre"].value_counts().reset_index()
        counts.columns = ["genre", "movie_count"]
        fig = px.pie(
            counts,
            names="genre",
            values="movie_count",
            title="Genre Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Movie Data Table")

st.dataframe(
    filtered.sort_values("rating", ascending=False),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download Filtered Data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_movies.csv",
    mime="text/csv"
)

st.caption("Built with Python, Streamlit, Pandas and Plotly.")