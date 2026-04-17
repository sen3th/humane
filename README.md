[![Netlify Status](https://api.netlify.com/api/v1/badges/219f98aa-2b0d-43e9-9523-5f396833e004/deploy-status)](https://app.netlify.com/projects/humane-the-game/deploys)
# Humane

Humane is a social elimination game where you get to join a room with a bunch of AI bots. They will try to eliminate you based on your messages on the chat. In order to win, you have to make them think you're a bot.

This project is inspired by the game [The Seventh One](https://github.com/ElliottStarosta/The-Seventh-One) by [Elliott Starosta](https://github.com/ElliottStarosta), Naomi Cheng and Annie Liang who won the first place in [Hack Club Campfire](https://campfire.hackclub.com/) in Ottawa.

It's built with [FastAPI](https://fastapi.tiangolo.com/) as the backend and [Svelte](https://svelte.dev/) as the frontend. The bots are powered by qwen3-32b provided free for teens by [HackClub](https://www.hackclub.com/). The backend is deployed on [Render](https://render.com/) and the frontend is deployed on [Netlify](https://www.netlify.com/). [TailwindCSS](https://tailwindcss.com/) is used for styling.

## Local Development

In order to run the project locally, you need to have python installed on your machine. Then, you can follow the steps below:
1. Clone the repository
2. Navigate to the backend directory and create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   ```
3. Activate the virtual environment:
     ```bash
     venv\Scripts\Activate.ps1
     ```
4. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```
5. Open a new terminal, navigate to the frontend directory and install the dependencies:
   ```bash
    cd frontend
    npm install
6. Run the frontend server:
   ```bash
   npm run dev
   ```
7. Open your browser and go to `http://localhost:5173` to access the frontend.

## Contributing
Contributions are welcome! If you want to contribute to the project, you can fork the repository and create a pull request! Thanks :)