# Taiwanese Correction Main Backend Ver 2.0

#### Current running on server `140.116.245.155` inside Docker container, you can find the file at `/home/p76121479/Linux_DATA/KuangFu/Taibun/main_backend`

## Features

- **Cross-Origin Resource Sharing (CORS):** The app allows cross-origin connections.
- **SQL Connection:** The application integrates with a shared SQL connection to fetch and update student data.
- **Dynamic Correction Template Fetching:** Depending on the specified year (e.g., `2023_02`, `2024_07`), the app fetches different student correction data and templates.
- **Progress Calculation:** The script calculates the percentage of completed corrections based on the assessments provided.
- **Proxy Fix Middleware:** To handle situations where the app is behind a reverse proxy, the app uses the `ProxyFix` middleware from `werkzeug`.
- **Thread-safe operations:** A global lock (`LOCK`) is used to ensure that multi-threaded processes don't interfere with one another.

## Folder Structure

- **app.py**: Application entrypoint, handle all API calls, see detail methods in `app.py`
- **filter_students.py**: Handles filtering of student data or fetching student-related information.
- **shared_sql_connection.py**: Provides a shared mysql cursor to interact with the SQL database.
- **.env**: stores mysql connection config for PyMySQL
- **.secret**: stores MySQL user password and root password
- **../mysql_data/**: volume that mysql docker mounts, you should backup data and remove this directory first if you want to rebuild the image & container
- **../Taibun_correction_web_db_backups/**: directory that stores 1 .sql file for mysql container startup initialization

## Installation (Docker, Preferred)

We use Docker to containerize our app, to run the container, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```
2. **Remove `../mysql` directory**:
    Container will mount 2 directory when starting, `../mysql` & `../Taibun_correction_web_db_backups`, you should backup `../mysql` and remove it first.
    ```sh
   docker exec -it <container-id> bash
   ```
   Backup MySQL Database
   ```sh
   mysqldump -u root -p <Database-name> -r <filename>.sql
   ```
3. **Put 1 `.sql` backup file into `../Taibun_correction_web_db_backups`**: mysql container will initialize by reading this directory, it'll import database into mysql
4. **Create a `.secret` directory inside the project directory**: you should create this directory first, and create 2 file inside it, `mysql_root_password.txt` & `mysql_user_password.txt`, enter password you preferred, it's recommended that you use different password.
5. **Create a `.env` file**: change `.env_example` to `.env`, and insert required arguments.
6. **Start Container**:
    ```sh
   docker compose up --build -d
   ```
7. **Remove Container**:
    ```sh
   docker compose down
    ```
## Installation (Local)

1. **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Set up the virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install the required dependencies**:
    Install Flask and other required libraries using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database**:
    - Ensure you have access to the SQL server that the application uses.
    - Update the connection details in the `shared_sql_connection.py` file.
    - choose 1 `.sql` backup from `Taibun_correction_web_db_backups` directory, restore it in your mysql server

5. **Run the app**:
    To start the development server, run the following command:
    ```bash
    waitress-serve --host=0.0.0.0 --port=<PORT> app:app
    ```

## Function stores in Dictionary

The app defines routes to fetch and manage student data. Depending on the specific correction year, different functions are used for fetching data and creating correction templates.

- **Fetch Student Data**: The application supports fetching student correction data based on the year.
- **Create Correction Templates**: The app dynamically generates correction templates for different years based on the logic provided in `CREATE_CORRECTION_TEMPLATE`.


## Configuration

To customize the behavior of the app or change database connections, modify the following configuration files:

- **shared_sql_connection.py**: Update the SQL connection details here.

## Dependencies

- `Python 3.10.14`
- `Flask`
- `Flask-CORS`
- `PyMySQL`
- `werkzeug` for middleware handling
- `python-dotenv`
- `cryptography`
- `pandas` for data output to `.xlsx` file (not implement yet)
