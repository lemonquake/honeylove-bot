# Honeylove Announcer Bot

A custom Discord bot designed for the Honeylove community to handle announcements, scheduling, and automated onboarding.

## Features

### 📢 Announcements
Easily send formatted announcements to any channel using the slash command:
*   **/announce**: Opens a modal to create a rich embed announcement.
    *   **Arguments**:
        *   `channel`: The channel to send the message to.
        *   `color`: (Optional) Hex color code for the embed side bar (e.g., `#FFD700`).
        *   `image_url`: (Optional) URL of an image to embed.
        *   `ping`: (Optional) Text to mention roles or users (e.g., `@everyone`).

### 📅 Scheduling
Automate your announcements to run on a recurring basis.
*   **/schedule**: Create a recurring announcement.
    *   Supports intervals in Minutes, Hours, or Days.
*   **/schedules**: View a list of all active schedules, including their next run time and ID.
*   **/unschedule**: Remove a scheduled task using its ID.

### 👋 Automated Onboarding
The bot automatically detects how new members join and welcomes them accordingly:
*   **Ambassador Invite Tracking**: Detects users joining via the Ambassador invite and welcomes them in the valid Ambassador channel.
*   **Creator Invite Tracking**: Detects users joining via the Creator invite and welcomes them in the Creator channel.
*   **Role detection**: If invite tracking fails, the bot also listens for role updates to trigger the welcome message.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/lemonquake/honeylove-bot.git
    cd honeylove-bot
    ```

2.  **Install Dependencies:**
    Ensure you have Python 3.8+ installed.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration:**
    Create a `.env` file in the root directory with your credentials:
    ```env
    DISCORD_TOKEN=your_bot_token_here
    APP_ID=your_application_id_here
    ```

4.  **Run the Bot:**
    ```bash
    python main.py
    ```

## Contributing
1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.
