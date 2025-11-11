# Sample API Collection

*This is a sample markdown file showing how to define API requests for Lumina*

## Get All Users

- Method: GET
- URL: https://jsonplaceholder.typicode.com/users
- Headers:
  - Accept: application/json
  - User-Agent: Lumina/1.0
- Params:
  - page: 1
  - limit: 10

---

## Get Single User

- Method: GET
- URL: https://jsonplaceholder.typicode.com/users/1
- Headers:
  - Accept: application/json

---

## Create New Post

- Method: POST
- URL: https://jsonplaceholder.typicode.com/posts
- Headers:
  - Content-Type: application/json
  - Accept: application/json
- Body:
```json
{
  "title": "Sample Post Title",
  "body": "This is the content of the post. It can be a long text.",
  "userId": 1
}
```

---

## Update Post

- Method: PUT
- URL: https://jsonplaceholder.typicode.com/posts/1
- Headers:
  - Content-Type: application/json
- Body:
```json
{
  "id": 1,
  "title": "Updated Post Title",
  "body": "Updated content here",
  "userId": 1
}
```

---

## Delete Post

- Method: DELETE
- URL: https://jsonplaceholder.typicode.com/posts/1
- Headers:
  - Accept: application/json

---

## Get Comments for Post

- Method: GET
- URL: https://jsonplaceholder.typicode.com/comments
- Headers:
  - Accept: application/json
- Params:
  - postId: 1

---

## Create Comment

- Method: POST
- URL: https://jsonplaceholder.typicode.com/comments
- Headers:
  - Content-Type: application/json
- Body:
```json
{
  "postId": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "body": "This is a great post!"
}
```

---

## Search Posts

- Method: GET
- URL: https://api.example.com/search
- Headers:
  - Authorization: Bearer {{API_TOKEN}}
  - Accept: application/json
- Params:
  - q: search term
  - page: 1
  - per_page: 20

---

## Upload File (Form Data Example)

- Method: POST
- URL: https://api.example.com/upload
- Headers:
  - Authorization: Bearer {{API_TOKEN}}
- Body:
```json
{
  "file": "file content here",
  "description": "My uploaded file"
}
```
