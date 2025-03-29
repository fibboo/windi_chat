# WinDi Chat

## Overview

WinDi Chat is a project that provides a chat application backend powered by FastAPI and SQLAlchemy, featuring
database migrations managed by Alembic. It includes built-in API documentation accessible via Swagger and Redoc, and
offers comprehensive test support either through Docker or locally using pytest.


## Quick Start

1. Clone the repository:
   ```bash
   git clone git@github.com:fibboo/windi_chat.git
   ```
2. Navigate to the project directory:
   ```bash
   cd windi_chat
   ```
3. Build the Docker images:
   ```bash
   docker compose build
   ```
4. Start the project:
   ```bash
   docker compose up -d
   ```
5. Create the database:
   ```bash
   docker compose exec postgres psql -U user -d postgres -c "CREATE DATABASE windi_chat;"
   ```
6. Apply database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
7. Populate the database with test data (optional):
   ```bash
   docker compose exec backend python app/test_scripts/generate_test_data.py
   ```
   
Once all steps are completed, your project will be available at:  
[http://localhost:8000](http://localhost:8000)

---

## Running Tests

You can verify the functionality of the project by running the tests. There are two ways to do so:

1. **Inside the Docker container** (service should be running):
   ```bash
   docker compose exec backend pytest -n auto
   ```

2. **Locally (if you have Python installed)**:
   Ensure your virtual environment is activated, then run:
   ```bash
   pytest -n auto
   ```
   
---

## API Documentation

The project provides built-in API documentation, available via Swagger or Redoc. To access it, open the following URL after starting the project:

Swagger - [http://localhost:8000/docs](http://localhost:8000/docs)

Redoc - [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Examples of API Requests

### Sending a Message (`/messages`)

To send a message in the chat, you need to make a POST request to the `/messages` endpoint. Here's an
example using `curl`:

```bash
curl -X POST http://localhost:8000/messages \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <your-token>" \
-d '{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa0",
  "chat_id": 2510,
  "text": "Hello, how are you?"
}'
```
In the example above:
- `id` is unique UUID message id.

### Getting Chat History (`/chats/{chat_id}/history`)

To retrieve the message history of a specific chat, make a GET request to the `/chats/{chat_id}/history` endpoint. Here's an
example using `curl`:

```bash
curl -X GET "http://localhost:8000/chats/1/history?page=1&psize=20" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <your-token>"
```

In the example above:

- `1` is the `chat_id`.
- `page` defines the current page, and `size` determines how many messages you want to fetch per page.
- `<your-token>` must be replaced with your actual authorization token.

### Connecting to WebSocket (`/ws/{chat_id}`)

The project provides a WebSocket endpoint for real-time communication. You can connect to this WebSocket using the following details:

- **Endpoint**: `/chats/ws/{chat_id}`
   - `{chat_id}` should be replaced with the ID of the chat you want to connect to.

- **Headers**:
   - `Authorization`: Bearer \<your-token\> (e.g., `Authorization: Bearer <your-token>`)
   - `device_id`: A unique identifier for the device connecting to the WebSocket.

#### Example using JavaScript:
```javascript
// Example using browser's WebSocket API
const chatId = 1;
const token = "your-auth-token";
const deviceId = "unique-device-identifier";

// Create WebSocket connection
const socket = new WebSocket(`ws://localhost:8000/chats/ws/${chatId}`);

// Add headers to connection
socket.onopen = function() {
  // Authentication message sent immediately after connection
  const authMessage = {
    type: "authorization",
    token: token,
    device_id: deviceId
  };
  socket.send(JSON.stringify(authMessage));
  console.log("Connected to WebSocket");
};

// Handle incoming messages
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log("Message received:", message);
};

// Handle errors
socket.onerror = function(error) {
  console.error("WebSocket Error:", error);
};

// Handle connection close
socket.onclose = function() {
  console.log("WebSocket connection closed");
};

// Send a message
function sendMessage(text) {
  const message = {
    type: "message",
    text: text,
    timestamp: new Date().toISOString()
  };
  socket.send(JSON.stringify(message));
}

