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
| POST   | /auth/login                              | Public            | login               |
| POST   | /patients/{id}/send                              | Public            | send a new patient               |
| POST   | /patients/{id}/send{doctor_id}                              | Public            | send a new patient to a specific doctor  |

##  Login
json payload : `{"username":"admin","password":"pass"}`
HTTP Headers : `Authorization = Bearer <access_token>` 

## register
json payload : `{"username":"admin","password":"pass", "role": "roleType"}`

## create and send patient to all doctors
json payload : `{"name":"name","contact_info":"contactinf", "medical_history": "roleType"}`