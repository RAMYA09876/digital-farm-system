from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farm_name = Column(String)
    location = Column(String)


class Livestock(Base):
    __tablename__ = "livestock"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer)
    species = Column(String)
    age = Column(Integer)


class AntimicrobialUsage(Base):
    __tablename__ = "amu"

    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer)
    drug_name = Column(String)
    dosage = Column(Float)
    start_date = Column(Date)
    withdrawal_days = Column(Integer)
    withdrawal_date = Column(Date)
    mrl_limit = Column(Float)
    residue_value = Column(Float)
    status = Column(String)