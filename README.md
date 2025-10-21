# Health-Tracker

This repository contains a Health-Tracker application with separate frontend and backend folders. This README explains how to set up and run both parts locally (development) and build them for production.

## Prerequisites

- Node.js (>= 16) and npm or Yarn
- Git
- (Optional) Docker & Docker Compose if you prefer containerized setup
- (Optional) A database (PostgreSQL or MongoDB) depending on the backend configuration

## Repository layout

- /frontend  - the frontend application (React/Vue/Angular — adjust to your stack)
- /backend   - the backend application (Node/Express, or similar)

If your project uses different folders, update the paths below accordingly.

---

## Frontend — Local development

1. Open a terminal and navigate to the frontend folder:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   Using npm:
   ```bash
   npm install
   ```

   Or using Yarn:
   ```bash
   yarn install
   ```

3. Create a .env file in the frontend folder (if required) based on the example below:

   Example .env
   ```env
   REACT_APP_API_URL=http://localhost:4000/api
   # other REACT_APP_* variables your app expects
   ```

4. Start the development server:

   ```bash
   npm start
   # or
   yarn start
   ```

   The frontend dev server typically runs at http://localhost:3000. Adjust the port if your project uses a different default.

5. Build for production:

   ```bash
   npm run build
   # or
   yarn build
   ```

   The production-ready static files will be written to the `build` (or `dist`) folder.

---

## Backend — Local development

1. Open a terminal and navigate to the backend folder:

   ```bash
   cd backend
   ```

2. Install dependencies:

   ```bash
   npm install
   # or
   yarn install
   ```

3. Create a .env file in the backend folder with required environment variables. Example:

   Example .env
   ```env
   PORT=4000
   NODE_ENV=development
   DATABASE_URL=postgres://user:password@localhost:5432/health_tracker_db
   # Or for MongoDB:
   # MONGODB_URI=mongodb://localhost:27017/health_tracker_db
   JWT_SECRET=your_jwt_secret_here
   # Any other variables your backend requires
   ```

4. Database setup (example PostgreSQL / MongoDB instructions):

   - PostgreSQL:
     - Create a database and a user with privileges.
     - Run any migrations or seeders your project provides. For example, if you use Knex or Sequelize:
       ```bash
       npx knex migrate:latest
       # or
       npx sequelize db:migrate
       ```

   - MongoDB:
     - Ensure mongod is running and the MONGODB_URI is set correctly.
     - Run any seed scripts if provided.

5. Start the backend server in development:

   ```bash
   npm run dev
   # or
   yarn dev
   ```

   The backend typically listens on the port specified in your .env (e.g., 4000).

6. Start the backend in production:

   ```bash
   npm start
   # or, if you use a build step (TypeScript):
   npm run build && npm start
   ```

---

## Running frontend and backend together

Option A — Run them in separate terminals

- Start the backend in one terminal (cd backend && npm run dev)
- Start the frontend in another terminal (cd frontend && npm start)

Option B — Root-level script (optional)

If you want to start both with a single command, you can install `concurrently` at the repository root and add a script:

```json
"scripts": {
  "dev": "concurrently \"cd backend && npm run dev\" \"cd frontend && npm start\""
}
```

Then run:
```bash
npm run dev
```

Option C — Docker & Docker Compose

Create a docker-compose.yml at the repo root (example skeleton):

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "4000:4000"
    env_file:
      - ./backend/.env
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:4000/api

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: health_tracker_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

Adjust the compose file to match your app's details.

---

## Environment variable examples

Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:4000/api
```

Backend (.env)
```env
PORT=4000
NODE_ENV=development
DATABASE_URL=postgres://user:password@localhost:5432/health_tracker_db
JWT_SECRET=some-secret
```

Never commit .env files with secrets to the repository. Keep them out of version control.

---

## Troubleshooting

- "Frontend cannot reach backend": Verify REACT_APP_API_URL and that the backend server is running and CORS is configured correctly.
- "Database connection errors": Check DATABASE_URL / MONGODB_URI, ensure the database is running and credentials are correct.
- "Port already in use": change the PORT in .env or stop the process using that port.
- Check package.json scripts in frontend/backend if the commands above differ.

---

## Tests

If your project has tests, run them from the respective folder:

```bash
cd backend
npm test

cd frontend
npm test
```

---

## Contributing

If you want to contribute, open a pull request describing your changes. Follow any code style or linting rules in the repository.

---

## Contact

If you have questions, open an issue in this repository or contact the maintainers.
