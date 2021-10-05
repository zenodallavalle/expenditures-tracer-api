# API_V2

With the transition to api_v2, I want to improve some aspects.

- user can now authenticate without the need of user_id
- categories, cashes, are included in database representation.
- category and cash create, update, delete operations are still done at `/categories`, `/cashes` api endpoints.
- expenditures are retrieved, created, updated and deleted from `/expenditures`.
- for databases: when user instance is retrieved, databases minimal info are included (id, name, ...). When you set a workingDB, retrieve it from `/dbs/[id]`. This stands also for create, update and delete database.
- When an operation is performed, database representation is also included.
- Months will be included in database representation.
