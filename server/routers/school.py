from fastapi import APIRouter, Body, HTTPException
from typing import List
from pydantic import BaseModel
from server.helpers.database import student_collection
from server.helpers.blockchain import blockchain

school_router = APIRouter()

@school_router.post("/create-students")
async def create_student(names: List[str], ids: List[int]) -> dict:
    if len(names) != len(ids):
        raise HTTPException(status_code=400, detail="Invalid input")

    items = []
    for i, name in enumerate(names):
        item = {
            "_id": ids[i],
            "name": name,
            "status": "pending"
        }

        items.append(item)

    student_collection.insert_many(items)

    return {
        "message": "oke"
    }

class VerifyData(BaseModel):
    ids: List[int]

@school_router.post("/verify")
async def verify_doc(data: VerifyData = Body(...)) -> dict:
    students = student_collection.find(
        {
            "_id": {
                "$in": data.ids
            }
        },
        {
            "_id": 1,
            "address": 1,
            "root": 1
        }
    )

    student_addresses = []
    student_ids = []
    student_hashes = []

    for student in students:
        student_addresses.append(blockchain.w3.toChecksumAddress(student["address"]))
        student_ids.append(student["_id"])
        student_hashes.append(student["root"])

    if len(student_ids) == 0 or len(student_addresses) == 0 or len(student_hashes) == 0:
        raise HTTPException(status_code=400, detail="Invalid student id")

    hash: str = blockchain.mint_nft(addresses=student_addresses, token_ids=student_ids, roots=student_hashes)

    student_collection.update_many({
        "_id": {
            "$in": data.ids
        }
    }, {
        "$set": {
            "status": "verified"
        }
    })

    return {
        "message": {
            "hash": hash
        }
    }

@school_router.get("/students")
async def get_students(limit: int = 10, page: int = 1) -> dict:
    skip = limit * (page - 1)
    return {
        "message": list(student_collection.find({}).skip(skip=skip).limit(limit=limit))
    }

@school_router.post("/delete-all")
async def delete() -> dict:
    student_collection.delete_many({})
    return {
        "message": "oke"
    }
