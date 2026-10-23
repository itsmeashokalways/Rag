from embedding import generate_embeddings
from db import insert_records

# single function to run the pipeline
def insert():
    result = generate_embeddings()
    print(result)
    insert_records(result)

# initial insertion 
insert()


