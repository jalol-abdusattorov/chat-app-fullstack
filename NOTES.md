1. What do a user, a chat and a message look like in the database?
2. How does the server know who is in a chat?
3. For every action in the app: should it be a normal HTTP request or go through the WebSocket? Ask yourself: does someone 4 else need to see this instantly? Not everything needs a WebSocket.
4. What events will the server push to the browser? Write a list, one line per event.