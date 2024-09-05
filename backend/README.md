# Leaderboard system - backend

This repository contains the source code for a contest management system with ELO rating calculations. The system allows
users to sign up for contests, and administrators to process ELO ratings based on contest results.

## Features

- **User Signup for Contests**: Users can sign up for contests before they start.
- **ELO Calculation**: Calculate and update ELO ratings for users based on their performance in contests.
- **Admin Authentication**: Secure endpoints for administrative actions using JWT tokens.

## Installation

1. Clone the repository:
    ```bash
    git clone git@github.com:CJskii/leaderboard-system.git
    ```

2. Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:  
   Create a `.env` file in the root directory and add the following variables:
    ```bash
    SECRET_KEY=your_secret_key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ADMIN_TOKEN=your_secure_admin_token
    ```

5. Run the application:
    ```bash
    uvicorn main:app --reload
    ```

## Usage

### Endpoints

#### Public Endpoints:

- **Root**  
  `GET /`  
  Example request:
  ```bash
  curl http://localhost:8000/
    ```

### User Signup for Contest

**POST** `/contests/{contest_id}/signup/{user_id}`  
**Example request:**

```bash
curl -X POST "http://localhost:8000/contests/1/signup/1"
```
## User Endpoints

### Create User

**POST** `/users/`  
**Example request:**

```bash
 curl -X POST -H "Content-Type: application/json" -d '{"username": "user1", "password": "password1", "email": "user1@example.com"}' http://localhost:8000/users/
```
### Login

**POST** `/token`  
**Example request:**

```bash
curl -X POST -F "username=user1" -F "password=password1" http://localhost:8000/token
```

### Get All Users

**GET** `/users`  
**Example request:**

```bash
curl http://localhost:8000/users/
```

### Get Current User

**GET** `/users/me`  
**Example request:**

```bash
curl -H "Authorization: Bearer <your_access_token>" http://localhost:8000/users/me
```

## Admin Endpoints (Protected):

### Process ELO Calculation

**POST** `/contests/{contest_id}/process_elo`  
**Example request:** Requires admin token in headers

```bash
curl -X POST "http://localhost:8000/contests/1/process_elo" -H "admin-token: your_secure_admin_token"
```

### Process Participation Days

**POST** `/contests/{contest_id}/process_participation_days`  
**Example request:** Requires admin token in headers

```bash
curl -X POST "http://localhost:8000/contests/1/process_participation_days" -H "admin-token: your_secure_admin_token"
```

## Running Tests

1. **Set up the test database**: Ensure you have a test database configured in your environment.
2. **Run tests**:
    ```bash
    make test
    ```

---

### Contributing

1. **Fork the repository**.
2. **Create a new branch**:
    ```bash
    git checkout -b feature/your-feature
    ```
3. **Commit your changes**:
    ```bash
    git commit -m 'Add some feature'
    ```
4. **Push to the branch**:
    ```bash
    git push origin feature/your-feature
    ```
5. **Open a pull request**.

---

### License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
