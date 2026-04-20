from pydantic import BaseModel
from datetime import date
from typing import List


# ============================
# FARM
# ============================

class FarmCreate(BaseModel):
    farm_name: str
    location: str


class FarmResponse(FarmCreate):
    id: int

    class Config:
        orm_mode = True


# ============================
# LIVESTOCK
# ============================

class LivestockCreate(BaseModel):
    farm_id: int
    species: str
    age: int


class LivestockResponse(LivestockCreate):
    id: int

    class Config:
        orm_mode = True


# ============================
# AMU
# ============================

class AMUCreate(BaseModel):
    animal_id: int
    drug_name: str
    dosage: str
    start_date: date
    withdrawal_days: int
    mrl_limit: float


class AMUResponse(BaseModel):
    id: int
    animal_id: int
    drug_name: str
    dosage: str
    start_date: date
    withdrawal_days: int
    withdrawal_date: date
    mrl_limit: float
    residue_value: float
    status: str

    class Config:
        orm_mode = True

class AlertResponse(BaseModel):
    animal_id: int
    drug: str
    withdrawal_date: date
    status: str    

    class Config:
        orm_mode = True