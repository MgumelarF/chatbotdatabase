from db import faq_collection

def get_all_faq():
    return list(faq_collection.find({}))

def add_faq(question, answer, category_id):
    faq_collection.insert_one({
        "question": question,
        "answer": answer,
        "category_id": category_id
    })

def delete_faq(faq_id):
    faq_collection.delete_one({"_id": faq_id})