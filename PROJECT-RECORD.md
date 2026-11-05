
# IS218 Review 1 — Creative Game Project Record

## Project: Iron Man — Drone Assault

### 1. Two Game Concepts

**Concept A: Iron Man — Drone Assault**

My first idea is a superhero-inspired combat game where the player controls Iron Man, flies around the screen, and fights enemy drones. The game currently has five regular drones followed by a boss fight. The player can shoot repulsors, launch missiles, and use Shift to boost and dodge attacks.

**Concept B: Iron Man — Flight Academy**

My second idea is a flying challenge game where the player navigates through checkpoints and avoids obstacles while trying to finish as fast as possible. Players could compete for better completion times and save their results.

**My Choice: Iron Man — Drone Assault**

I chose Drone Assault because I already have a working 2D prototype and want to improve something I started rather than build a completely new game. I also think combat is more interesting because players have to manage their health, avoid attacks, and defeat a boss. It gives me clear results to save, like wins, losses, and enemies defeated.


### 2. Target Audience

My target audience is college students and casual gamers who enjoy
superhero games and short arcade-style challenges. I want the game
to be easy to access through a web browser without requiring
players to download anything.

### 3. Dream

My long-term dream is to create a cinematic 3D Iron Man-inspired
game where players can fly around a city, fight enemies, unlock
different suits, and complete missions.

I want players to have their own accounts so they can track
their progress, view their previous missions, and improve
their performance over time.

### 4. Working Promise

For the complete version of my project, a player should be
able to:

1. Create an account.
2. Log in securely.
3. Select a game mode and complete a mission.
4. Have their mission results saved to their account.
5. View their previous results on a private dashboard.
6. Update their display name or password.
7. Log out securely.

The game currently has two implemented modes: Drone Assault
and Flight Academy. The account system, database, saved
results, and dashboard are planned features that still need
to be developed.

### 5. Creative Experiment

One thing I am uncertain about is whether a 2D or 3D
gameplay style will provide the better player experience.

I started with a 2D JavaScript Canvas game because it is
easier to develop, test, and run in a browser. I also
experimented with Three.js to explore a possible 3D version.

My experiment is to compare the two approaches based on
player controls, visual appearance, browser performance,
and development complexity.

For now, I am keeping the 2D version as the main playable
prototype while exploring 3D as a possible future improvement.


### 6. Five User Stories

**User Story 1 — Account Registration**

As a new player, I want to create an account so that
I can save my progress and access my results later.

**User Story 2 — Secure Login**

As a returning player, I want to log in securely so
that I can access my own game history and dashboard.

**User Story 3 — Play a Mission**

As a player, I want to select Drone Assault and fight
enemy drones and the boss so that I can complete a
challenging mission and improve my skills.

**User Story 4 — View Saved Results**

As a player, I want my completed mission results to
be saved so that I can view my wins, losses, and
performance on my private dashboard.

**User Story 5 — Manage My Account**

As a player, I want to update my display name or
password and log out securely so that I can manage
my account and protect my information.


### 7. Architecture and Technology Stack

I am building Iron Flight as a browser-based game using
Python Flask, JavaScript, HTML, and CSS.

Flask runs the web application and serves the game pages.
JavaScript Canvas handles the gameplay, including player
movement, enemies, shooting, and checkpoints.

For the full version, I plan to use SQLite to store player
accounts and mission results.

The planned application flow is:

Browser → Flask Application → SQLite Database

Right now, the game runs locally with two playable modes.
The database and account features are planned for later.

### 8. Design Pattern

For my game, I plan to use the Strategy Pattern to
manage different enemy behaviors.

For example, regular drones could follow one attack
strategy, while the boss uses a different strategy
with stronger attacks and movement patterns.

The simpler alternative would be using if/else
statements to control each enemy's behavior.

I would choose the Strategy Pattern if I add more
enemy types because it would make the code easier
to organize and update.

For now, I am keeping the gameplay code simple
while I continue building the prototype.

### 9. AI Reflection

I used ChatGPT to help me plan my game, organize my
project files, and write some of the Python, JavaScript,
HTML, and CSS code.

AI helped me build the two game modes, Drone Assault
and Flight Academy, and set up automated tests using
pytest.

One thing I learned is that AI-generated code still
needs to be tested. Just because the code looks correct
does not mean everything will work properly.

I tested both game modes in my browser and ran seven
automated tests. All seven tests passed.

Next time, I want to use AI to help me improve the
gameplay while making sure I understand and test
the changes myself.


### 9. AI Reflection

I used ChatGPT to help me plan my game, organize my
project files, and write some of the Python, JavaScript,
HTML, and CSS code.

AI helped me build the two game modes, Drone Assault
and Flight Academy, and set up automated tests using
pytest.

One thing I learned is that AI-generated code still
needs to be tested. Just because the code looks correct
does not mean everything will work properly.

I tested both game modes in my browser and ran seven
automated tests. All seven tests passed.

Next time, I want to use AI to help me improve the
gameplay while making sure I understand and test
the changes myself.

### 10. Testing and Feedback

I tested Iron Flight locally using my web browser
and automated tests with pytest.

**Automated Testing:**

I ran the following command:

python -m pytest -v

Results: 7 tests passed in 0.60 seconds.

The tests checked:
- Flask homepage loads successfully.
- Game title appears correctly.
- Both game modes appear on the page.
- Game Canvas exists.
- Drone Assault JavaScript file loads.
- Flight Academy JavaScript file loads.
- CSS stylesheet loads.

**Manual Testing:**

I opened both Drone Assault and Flight Academy
in my browser and confirmed that both game modes
were playable.

**Feedback:**

I have not collected peer feedback yet. My next
step is to ask another student to try both modes
and give feedback on the controls, difficulty,
and overall gameplay experience.

**What I Learned:**

Automated tests help confirm that the application
loads correctly, while manual testing helps check
whether the game actually works for players.

### 11. Next Steps

My next goal is to continue improving Iron Flight
and turn it into a more complete web application.

**Short-Term Goals:**
- Improve the controls and gameplay in both modes.
- Fix any bugs found during testing.
- Ask another student to play the game and provide feedback.
- Add more automated tests for game functionality.

**Future Development:**
- Create a player registration and login system.
- Use SQLite to store player accounts and game results.
- Build a dashboard where players can view their progress.
- Allow players to update their account information.
- Explore adding 3D gameplay using Three.js.

**For My Next Review:**

I want to demonstrate improved gameplay, show
additional testing results, and make progress
toward implementing player accounts and saved scores.

My main focus is to build the project step by step
and make sure each feature works before adding
more complicated functionality.
