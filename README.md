# CS203_Lab_01
This repository is made for the submission of the Assignment 1 of the course CS 203 - Software Tools and Techniques for AI, at the Indian Institute of Technology, Gandhinagar.

## Setup
1. Clone the repository using <br>
```bash
git clone https://www.github.com/HarshilShah1804/CS203_Assignment1.git
```
2. Change the current working directory <br>
```bash
cd CS203_Assignment1
```
3. Install the required modules <br>
```bash
pip install -r requirements.txt
```
4. Run the flask Application
```bash
python app.py
```
5. Go to `127.0.0.1:5000` on your browser to access the website.
### For Jaeger
1. Install docker desktop
2. Create a file `docker-compose.yml` file with content:
```
version: '3.7'
services:
  jaeger:
    image: jaegertracing/all-in-one:1.39
    environment:
      - COLLECTOR_ZIPKIN_HTTP_PORT=9411
    ports:
      - 5775:5775
      - 6831:6831/udp
      - 6832:6832/udp
      - 5778:5778
      - 16686:16686
      - 14250:14250
      - 14267:14267
      - 14268:14268
      - 9431:9431
```
3. Run the command in terminal.
```bash
docker-compose up
```   
3. Go to `127.0.0.1:16686` on your browser to access the Jaeger UI.

## Screenshots: 
### User Interface of the website.
1. Home Page
![Home Page](https://github.com/user-attachments/assets/e31f3669-a364-44d8-b440-f615c4fdba58)

2. Course Catalog
![Course Catalog](https://github.com/user-attachments/assets/6b5e7f9f-bcce-4007-9c60-7a53a50126f5)

3. Add Course
![Add Course](https://github.com/user-attachments/assets/18ff8d42-98e4-4d89-b8c4-eb535df56309)

4. Course Details
![Course Details](https://github.com/user-attachments/assets/07e8d7a8-777c-4bc2-97b8-2a87b77d57a3)

5. Error on Adding Course
![Error on Adding](https://github.com/user-attachments/assets/a459b001-d0af-4e6e-b055-f45b2b9841a6)

6. Warning on Adding Course
![Warning on Adding](https://github.com/user-attachments/assets/7dca30f7-2d11-4488-bf3d-a12a82e6f914)

7. Course Deletion
![Course Deletion](https://github.com/user-attachments/assets/8f936a27-2a59-4ead-ad43-dc03e38bd984)

### Jaeger UI
1. Jaeger UI
![Jaeger UI](https://github.com/user-attachments/assets/a76883b0-fa92-4736-b026-33583caeb5db)
2. Index:
![image](https://github.com/user-attachments/assets/f9681f05-9fac-43dd-acb8-86503773f4ba)

3. Catalog:
![image](https://github.com/user-attachments/assets/60052875-01a1-4122-85e3-3f280626ddc7)

4. Add Course:
![image](https://github.com/user-attachments/assets/551810f1-a9ed-4814-8f69-cbbcaf87bba5)

5. View Course
![image](https://github.com/user-attachments/assets/296c4556-812c-4e6d-ae83-896eb6c9de91)

6. Error on Adding Course
![image](https://github.com/user-attachments/assets/18411e81-ffc0-44a6-a55a-00f17ae68df7)

7. Warning on Adding Course
![image](https://github.com/user-attachments/assets/94be049c-77c7-4c94-b7b0-86b3b95eae31)

8. Total Error Recorded
![image](https://github.com/user-attachments/assets/b484b6f0-2642-4b2f-af86-ff07e14e1d40)

9. Total requests to a particular route.
![image](https://github.com/user-attachments/assets/07f6314c-a5a8-484f-a33b-fc3eef1faa01)
