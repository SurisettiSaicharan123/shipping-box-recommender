# AI Usage
 
## tools used
- Claude – I used Claude to help me understand the assignment, plan the Django project structure, build the initial code write and improve tests, and debug issues during developmnt

## Prompts I gave

1. give me the structure of this project

2. lets start building it. Create the Django project file which contains all the required file with code

3. I can only see Products and Boxes in the Django admin, but I don't see how to create an order or get the recommended box Can you check the project and add a simple complete flow for creating an order and getting the box recommendation, Please keep it clean and easy to demo for the hiring assignment

4. Everything is working corrctly now What are the next steps we should do to finish this assignment

## output I accepted  
1. I accepted the suggested Django project structure and used it as the base for my project.
2. I accepted the packing.py approach for keeping the box-selection logic separate from Django.
3. I accepted the packing algorithm with weight, volume, rotation, and guillotine packing checks.
4. I accepted the Order and OrderItem implementation to make the recommendation flow easier to use through Django Admin and the API
5. I also accepted the suggested tests and used them to verify the application.

## Output I rejected or modified
1. I modified the initial project by adding an Order and OrderItem flow so i could create orders and get box recommendations through django Admin
2. I also fixed the patch/file placement issue and verified the project again

## Mistakes the AI made
1. The Box.to_spec()  method returned the cost as a string instaed of a decimal, which was caught during testing
2. The Django Admin initially allowed an order to be saved without any items, so I fixed the validation

## How I verified the final code
I ran python manage.py test and confirmed that all 86 tests passed. I also tested the order flow in Django Admin and checked the API manually with different products to verify that the recommended box and no-fit cases worked correctly.
