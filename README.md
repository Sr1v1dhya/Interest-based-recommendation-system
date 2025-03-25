# Interest-Based Recommendation System

## Abstract

The Interest-Based Recommendation System aims to provide personalized content recommendations by leveraging user interests and social connections. This platform focuses on delivering relevant suggestions for movies, books, and TV shows, addressing the challenge of content overload through a targeted approach that enhances user engagement and satisfaction.

## Introduction

Traditional social networks often fail to provide customized recommendations, leaving users overwhelmed with irrelevant content. This project seeks to create a social platform that connects users with similar interests and recommends content based on their preferences and followers' activity.

## System Design

The system utilizes a structured SQL database with key entities such as:

- **USER**: Stores user details and preferences.
- **FOLLOW**: Represents user connections.
- **GENRE**: Captures user interest in different content genres.
- **MOVIES, BOOKS, and TVSHOWS**: Tables storing content details.

Users can follow others, select preferred genres and languages, and receive recommendations based on mutual interests and follower activity.

## Key Features

- **User Profiles**: Users personalize their profiles with genres and language preferences.
- **Recommendations**: A recommendation engine curates content based on user preferences and social connections.
- **Social Connectivity**: Users can follow others, view their preferences, and discover new content.
- **Content Tracking**: Previously consumed content is stored to avoid repetitive suggestions.

## Tech Stack

The system is developed using:

- **MySQL**: Manages structured data and relationships.
- **FastAPI**: Provides backend services, API endpoints, and web interface.
- **Jinja2**: Template engine for rendering HTML pages.
- **Bootstrap**: Enhances frontend styling and responsiveness.
- **JWT**: Handles user authentication and session management.

## Setup and Installation

### Prerequisites

- Python 3.8+
- MySQL Server
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone [repository-url]
   cd rec-sys
   ```

2. **Set up a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.sample .env
   ```

   Edit the `.env` file with your MySQL credentials and other configuration settings.

5. **Set up the database**

   - Create a MySQL database
   - Import the database schema using the provided schema.sql file:
     ```bash
     mysql -u username -p < schema.sql
     ```

6. **Run the application**

   ```bash
   uvicorn main:app --reload
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## Future Enhancements

Planned improvements include:

- Expanding content categories beyond movies, books, and TV shows.
- Enhancing the recommendation algorithm for improved accuracy.
- Implementing privacy controls for user preferences and recommendations.
- Adding content rating and review capabilities.
