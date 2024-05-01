# health360-be
Health360 CRM backend


## "install all the requirements:"
`pip3.11 install -r requirements.txt`?
## "run server"
uvicorn  main:app --reload

## API Endpoints
| Method | Endpoint                    | Access  Control   | Description                       |
|--------|-----------------------------|-------------------|-----------------------------------|
| GET    | /users/me                                   | Private           | Get current user info     |
| POST   | /auth/register                               | Public            | Register a new account               |
| POST   | /auth/login                              | Public            | Register a new account               |
| POST   | /patients/{id}/send                              | Public            | Register a new account               |
| POST   | /auth/register                             | Public            | Register a new account               |

##  Login
json payload : `{"username":"admin","password":"pass"}`
HTTP Headers : `Authorization = Bearer <access_token>` 

## register
No authentication required, just invalidate token</s>

##  Register user

## "to create the database schema run:"
`python3.11 creatSchema.py`